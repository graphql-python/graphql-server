import copy
from collections.abc import MutableMapping
from functools import partial
from typing import List

from graphql.error import GraphQLError
from graphql.type.schema import GraphQLSchema
from webob import Response

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


class GraphQLView:
    schema = None
    request = None
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
    charset = "UTF-8"

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

    def get_context(self, request):
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

    def dispatch_request(self, request):
        try:
            request_method = request.method.lower()
            data = self.parse_body(request)

            show_graphiql = request_method == "get" and self.should_display_graphiql(
                request
            )
            catch = show_graphiql

            pretty = self.pretty or show_graphiql or request.params.get("pretty")

            all_params: List[GraphQLParams]
            execution_results, all_params = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=request.params,
                batch_enabled=self.batch,
                catch=catch,
                # Execute options
                run_sync=not self.enable_async,
                root_value=self.get_root_value(),
                context_value=self.get_context(request),
                middleware=self.get_middleware(),
            )
            result, status_code = encode_execution_results(
                execution_results,
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
                return Response(
                    render_graphiql_sync(
                        data=graphiql_data,
                        config=graphiql_config,
                        options=graphiql_options,
                    ),
                    charset=self.charset,
                    content_type="text/html",
                )

            return Response(
                result,
                status=status_code,
                charset=self.charset,
                content_type="application/json",
            )

        except HttpQueryError as e:
            parsed_error = GraphQLError(e.message)
            return Response(
                self.encode(dict(errors=[self.format_error(parsed_error)])),
                status=e.status_code,
                charset=self.charset,
                headers=e.headers or {},
                content_type="application/json",
            )

    # WebOb
    @staticmethod
    def parse_body(request):
        # We use mimetype here since we don't need the other
        # information provided by content_type
        content_type = request.content_type
        if content_type == "application/graphql":
            return {"query": request.body.decode("utf8")}

        elif content_type == "application/json":
            return load_json_body(request.body.decode("utf8"))

        elif content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            return request.params

        return {}

    def should_display_graphiql(self, request):
        if not self.graphiql or "raw" in request.params:
            return False

        return self.request_wants_html()

    def request_wants_html(self):
        best = self.request.accept.best_match(["application/json", "text/html"])
        return best == "text/html"
