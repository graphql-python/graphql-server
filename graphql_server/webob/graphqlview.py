import copy
from collections import MutableMapping
from functools import partial

from graphql.error import GraphQLError
from graphql.type.schema import GraphQLSchema
from webob import Response

from graphql_server import (
    HttpQueryError,
    encode_execution_results,
    format_error_default,
    json_encode,
    load_json_body,
    run_http_query,
)

from .render_graphiql import render_graphiql


class GraphQLView:
    schema = None
    request = None
    root_value = None
    context = None
    pretty = False
    graphiql = False
    graphiql_version = None
    graphiql_template = None
    middleware = None
    batch = False
    charset = "UTF-8"

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

    def get_context_value(self):
        context = (
            copy.copy(self.context)
            if self.context and isinstance(self.context, MutableMapping)
            else {}
        )
        if isinstance(context, MutableMapping) and "request" not in context:
            context.update({"request": self.request})
        return context

    def get_middleware(self):
        return self.middleware

    format_error = staticmethod(format_error_default)
    encode = staticmethod(json_encode)

    def dispatch_request(self):
        try:
            request_method = self.request.method.lower()
            data = self.parse_body()

            show_graphiql = request_method == "get" and self.should_display_graphiql()
            catch = show_graphiql

            pretty = self.pretty or show_graphiql or self.request.params.get("pretty")

            execution_results, all_params = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=self.request.params,
                batch_enabled=self.batch,
                catch=catch,
                # Execute options
                root_value=self.get_root_value(),
                context_value=self.get_context_value(),
                middleware=self.get_middleware(),
            )
            result, status_code = encode_execution_results(
                execution_results,
                is_batch=isinstance(data, list),
                format_error=self.format_error,
                encode=partial(self.encode, pretty=pretty),  # noqa
            )

            if show_graphiql:
                return Response(
                    render_graphiql(params=all_params[0], result=result),
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
    def parse_body(self):
        # We use mimetype here since we don't need the other
        # information provided by content_type
        content_type = self.request.content_type
        if content_type == "application/graphql":
            return {"query": self.request.body.decode("utf8")}

        elif content_type == "application/json":
            return load_json_body(self.request.body.decode("utf8"))

        elif content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            return self.request.params

        return {}

    def should_display_graphiql(self):
        if not self.graphiql or "raw" in self.request.params:
            return False

        return self.request_wants_html()

    def request_wants_html(self):
        best = self.request.accept.best_match(["application/json", "text/html"])
        return best == "text/html"
