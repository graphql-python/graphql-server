import asyncio
import copy
from collections.abc import MutableMapping
from functools import partial
from typing import List

from graphql import GraphQLError, specified_rules
from graphql.pyutils import is_awaitable
from graphql.type.schema import GraphQLSchema
from sanic.headers import parse_content_header
from sanic.response import HTTPResponse, html
from sanic.views import HTTPMethodView

from graphql_server import (
    GraphQLParams,
    HttpQueryError,
    _check_jinja,
    encode_execution_results,
    format_error_default,
    json_encode,
    load_json_body,
    run_http_query,
)
from graphql_server.render_graphiql import (
    GraphiQLConfig,
    GraphiQLData,
    GraphiQLOptions,
    render_graphiql_async,
)
from graphql_server.utils import wrap_in_async


class GraphQLView(HTTPMethodView):
    schema = None
    root_value = None
    context = None
    pretty = False
    graphiql = False
    graphiql_version = None
    graphiql_template = None
    graphiql_html_title = None
    middleware = None
    validation_rules = None
    execution_context_class = None
    batch = False
    jinja_env = None
    max_age = 86400
    enable_async = False
    subscriptions = None
    headers = None
    default_query = None
    header_editor_enabled = None
    should_persist_headers = None

    methods = ["GET", "POST", "PUT", "DELETE"]

    format_error = staticmethod(format_error_default)
    encode = staticmethod(json_encode)

    def __init__(self, **kwargs):
        super(GraphQLView, self).__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        if not isinstance(self.schema, GraphQLSchema):
            # maybe the GraphQL schema is wrapped in a Graphene schema
            self.schema = getattr(self.schema, "graphql_schema", None)
            if not isinstance(self.schema, GraphQLSchema):
                raise TypeError("A Schema is required to be provided to GraphQLView.")

        if self.jinja_env is not None:
            _check_jinja(self.jinja_env)

    def get_root_value(self):
        return self.root_value

    def get_context(self, request):
        context = (
            copy.copy(self.context)
            if self.context is not None and isinstance(self.context, MutableMapping)
            else {}
        )
        if isinstance(context, MutableMapping) and "request" not in context:
            context.update({"request": request})
        return context

    def get_middleware(self):
        return self.middleware

    def get_validation_rules(self):
        if self.validation_rules is None:
            return specified_rules
        return self.validation_rules

    def get_execution_context_class(self):
        return self.execution_context_class

    async def __handle_request(self, request, *args, **kwargs):
        try:
            request_method = request.method.lower()
            data = self.parse_body(request)

            show_graphiql = request_method == "get" and self.should_display_graphiql(
                request
            )
            catch = show_graphiql

            pretty = self.pretty or show_graphiql or request.args.get("pretty")

            if request_method != "options":
                all_params: List[GraphQLParams]
                execution_results, all_params = run_http_query(
                    self.schema,
                    request_method,
                    data,
                    query_data=request.args,
                    batch_enabled=self.batch,
                    catch=catch,
                    # Execute options
                    run_sync=not self.enable_async,
                    root_value=self.get_root_value(),
                    context_value=self.get_context(request),
                    middleware=self.get_middleware(),
                    validation_rules=self.get_validation_rules(),
                    execution_context_class=self.get_execution_context_class(),
                )
                exec_res = (
                    await asyncio.gather(
                        *(
                            ex
                            if ex is not None and is_awaitable(ex)
                            else wrap_in_async(lambda: ex)()
                            for ex in execution_results
                        )
                    )
                    if self.enable_async
                    else execution_results
                )
                result, status_code = encode_execution_results(
                    exec_res,
                    is_batch=isinstance(data, list),
                    format_error=self.format_error,
                    encode=partial(self.encode, pretty=pretty),  # noqa: ignore
                )

                if show_graphiql:
                    graphiql_data = GraphiQLData(
                        result=result,
                        query=getattr(all_params[0], "query"),
                        variables=getattr(all_params[0], "variables"),
                        operation_name=getattr(all_params[0], "operation_name"),
                        subscription_url=self.subscriptions,
                        headers=self.headers,
                    )
                    graphiql_config = GraphiQLConfig(
                        graphiql_version=self.graphiql_version,
                        graphiql_template=self.graphiql_template,
                        graphiql_html_title=self.graphiql_html_title,
                        jinja_env=self.jinja_env,
                    )
                    graphiql_options = GraphiQLOptions(
                        default_query=self.default_query,
                        header_editor_enabled=self.header_editor_enabled,
                        should_persist_headers=self.should_persist_headers,
                    )
                    source = await render_graphiql_async(
                        data=graphiql_data,
                        config=graphiql_config,
                        options=graphiql_options,
                    )
                    return html(source)

                return HTTPResponse(
                    result, status=status_code, content_type="application/json"
                )

            else:
                return self.process_preflight(request)

        except HttpQueryError as e:
            parsed_error = GraphQLError(e.message)
            return HTTPResponse(
                self.encode(dict(errors=[self.format_error(parsed_error)])),
                status=e.status_code,
                headers=e.headers,
                content_type="application/json",
            )

    get = post = put = head = options = patch = delete = __handle_request

    # noinspection PyBroadException
    def parse_body(self, request):
        content_type = self.get_mime_type(request)
        if content_type == "application/graphql":
            return {"query": request.body.decode("utf8")}

        elif content_type == "application/json":
            return load_json_body(request.body.decode("utf8"))

        elif content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            return request.form

        return {}

    @staticmethod
    def get_mime_type(request):
        # We use mime type here since we don't need the other
        # information provided by content_type
        if "content-type" not in request.headers:
            return None

        mime_type, _ = parse_content_header(request.headers["content-type"])
        return mime_type

    def should_display_graphiql(self, request):
        if not self.graphiql or "raw" in request.args:
            return False

        return self.request_wants_html(request)

    @staticmethod
    def request_wants_html(request):
        accept = request.headers.get("accept", {})
        return "text/html" in accept or "*/*" in accept

    def process_preflight(self, request):
        """Preflight request support for apollo-client
        https://www.w3.org/TR/cors/#resource-preflight-requests"""
        origin = request.headers.get("Origin", "")
        method = request.headers.get("Access-Control-Request-Method", "").upper()

        if method and method in self.methods:
            return HTTPResponse(
                status=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": ", ".join(self.methods),
                    "Access-Control-Max-Age": str(self.max_age),
                },
            )
        else:
            return HTTPResponse(status=400)
