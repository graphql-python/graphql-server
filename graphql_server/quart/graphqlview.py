import copy
import sys
from collections.abc import MutableMapping
from functools import partial
from typing import List

from graphql import ExecutionResult
from graphql.error import GraphQLError
from graphql.type.schema import GraphQLSchema
from quart import Response, render_template_string, request
from quart.views import View

from graphql_server import (
    GraphQLParams,
    HttpQueryError,
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
    render_graphiql_sync,
)


class GraphQLView(View):
    schema = None
    root_value = None
    context = None
    pretty = False
    graphiql = False
    graphiql_version = None
    graphiql_template = None
    graphiql_html_title = None
    middleware = None
    batch = False
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

        assert isinstance(
            self.schema, GraphQLSchema
        ), "A Schema is required to be provided to GraphQLView."

    def get_root_value(self):
        return self.root_value

    def get_context(self):
        context = (
            copy.copy(self.context)
            if self.context and isinstance(self.context, MutableMapping)
            else {}
        )
        if isinstance(context, MutableMapping) and "request" not in context:
            context.update({"request": request})
        return context

    def get_middleware(self):
        return self.middleware

    async def dispatch_request(self):
        try:
            request_method = request.method.lower()
            data = await self.parse_body()

            show_graphiql = request_method == "get" and self.should_display_graphiql()
            catch = show_graphiql

            pretty = self.pretty or show_graphiql or request.args.get("pretty")
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
                context_value=self.get_context(),
                middleware=self.get_middleware(),
            )
            exec_res = (
                [
                    ex if ex is None or isinstance(ex, ExecutionResult) else await ex
                    for ex in execution_results
                ]
                if self.enable_async
                else execution_results
            )
            result, status_code = encode_execution_results(
                exec_res,
                is_batch=isinstance(data, list),
                format_error=self.format_error,
                encode=partial(self.encode, pretty=pretty),  # noqa
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
                    jinja_env=None,
                )
                graphiql_options = GraphiQLOptions(
                    default_query=self.default_query,
                    header_editor_enabled=self.header_editor_enabled,
                    should_persist_headers=self.should_persist_headers,
                )
                source = render_graphiql_sync(
                    data=graphiql_data, config=graphiql_config, options=graphiql_options
                )
                return await render_template_string(source)

            return Response(result, status=status_code, content_type="application/json")

        except HttpQueryError as e:
            parsed_error = GraphQLError(e.message)
            return Response(
                self.encode(dict(errors=[self.format_error(parsed_error)])),
                status=e.status_code,
                headers=e.headers,
                content_type="application/json",
            )

    @staticmethod
    async def parse_body():
        # We use mimetype here since we don't need the other
        # information provided by content_type
        content_type = request.mimetype
        if content_type == "application/graphql":
            refined_data = await request.get_data(raw=False)
            return {"query": refined_data}

        elif content_type == "application/json":
            refined_data = await request.get_data(raw=False)
            return load_json_body(refined_data)

        elif content_type == "application/x-www-form-urlencoded":
            return await request.form

        # TODO: Fix this check
        elif content_type == "multipart/form-data":
            return await request.files

        return {}

    def should_display_graphiql(self):
        if not self.graphiql or "raw" in request.args:
            return False

        return self.request_wants_html()

    @staticmethod
    def request_wants_html():
        best = request.accept_mimetypes.best_match(["application/json", "text/html"])

        # Needed as this was introduced at Quart 0.8.0: https://gitlab.com/pgjones/quart/-/issues/189
        def _quality(accept, key: str) -> float:
            for option in accept.options:
                if accept._values_match(key, option.value):
                    return option.quality
            return 0.0

        if sys.version_info >= (3, 7):
            return (
                best == "text/html"
                and request.accept_mimetypes[best]
                > request.accept_mimetypes["application/json"]
            )
        else:
            return best == "text/html" and _quality(
                request.accept_mimetypes, best
            ) > _quality(request.accept_mimetypes, "application/json")
