from functools import partial
from typing import List

from flask import Response, render_template_string, request
from flask.views import View
from graphql.error import GraphQLError
from graphql.type.schema import GraphQLSchema

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
    render_graphiql_sync,
)


class GraphQLView(View):
    schema = None
    root_value = None
    pretty = False
    graphiql = False
    graphiql_version = None
    graphiql_template = None
    graphiql_html_title = None
    middleware = None
    batch = False

    methods = ["GET", "POST", "PUT", "DELETE"]

    def __init__(self, **kwargs):
        super(GraphQLView, self).__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        assert isinstance(
            self.schema, GraphQLSchema
        ), "A Schema is required to be provided to GraphQLView."

    # noinspection PyUnusedLocal
    def get_root_value(self):
        return self.root_value

    def get_context_value(self):
        return request

    def get_middleware(self):
        return self.middleware

    format_error = staticmethod(format_error_default)
    encode = staticmethod(json_encode)

    def dispatch_request(self):
        try:
            request_method = request.method.lower()
            data = self.parse_body()

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
                graphiql_data = GraphiQLData(
                    result=result, **all_params[0]._asdict()  # noqa
                )
                graphiql_config = GraphiQLConfig(
                    graphiql_version=self.graphiql_version,
                    graphiql_template=self.graphiql_template,
                    graphiql_html_title=self.graphiql_html_title,
                    jinja_env=None,
                )
                source = render_graphiql_sync(
                    data=graphiql_data, config=graphiql_config
                )
                return render_template_string(source)

            return Response(result, status=status_code, content_type="application/json")

        except HttpQueryError as e:
            parsed_error = GraphQLError(e.message)
            return Response(
                self.encode(dict(errors=[self.format_error(parsed_error)])),
                status=e.status_code,
                headers=e.headers,
                content_type="application/json",
            )

    # Flask
    def parse_body(self):
        # We use mimetype here since we don't need the other
        # information provided by content_type
        content_type = request.mimetype
        if content_type == "application/graphql":
            return {"query": request.data.decode("utf8")}

        elif content_type == "application/json":
            return load_json_body(request.data.decode("utf8"))

        elif content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            return request.form

        return {}

    def should_display_graphiql(self):
        if not self.graphiql or "raw" in request.args:
            return False

        return self.request_wants_html()

    def request_wants_html(self):
        best = request.accept_mimetypes.best_match(["application/json", "text/html"])
        return (
            best == "text/html"
            and request.accept_mimetypes[best]
            > request.accept_mimetypes["application/json"]
        )
