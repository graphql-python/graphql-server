from functools import partial
from typing import Type, Any, Optional, Collection

from aiohttp import web
from graphql import ExecutionResult, GraphQLError, specified_rules
from graphql.execution import Middleware
from graphql.type.schema import GraphQLSchema
from graphql.validation import ASTValidationRule

from graphql_server import (
    HttpQueryError,
    get_schema,
    encode_execution_results,
    format_error_default,
    json_encode,
    load_json_body,
    run_http_query,
    process_preflight,
)
from graphql_server.render_graphiql import (
    GraphiQLOptions,
    render_graphiql_sync,
)

from typing import Dict, Any

class GraphQLView:

    accepted_methods = ["GET", "POST", "PUT", "DELETE"]

    format_error = staticmethod(format_error_default)
    encode = staticmethod(json_encode)

    def __init__(self, schema: GraphQLSchema, *,
        root_value: Any = None,
        pretty: bool = False,
        graphiql: bool = True,
        middleware: Optional[Middleware] = None,
        validation_rules: Optional[Collection[Type[ASTValidationRule]]] = None,
        batch: bool = False,
        max_age: int = 86400,
        enable_async: bool = False,
        graphiql_options: Optional[GraphiQLOptions] = None,
    ):
        self.schema = get_schema(schema)
        self.root_value = root_value
        self.pretty = pretty
        self.graphiql = graphiql
        self.graphiql_options = graphiql_options
        self.middleware = middleware
        self.validation_rules = validation_rules
        self.batch = batch
        self.max_age = max_age
        self.enable_async = enable_async

    render_graphiql = render_graphiql_sync

    def get_root_value(self):
        return self.root_value

    def get_context(self, request):
        return {"request": request}

    def get_middleware(self):
        return self.middleware

    def get_validation_rules(self):
        if self.validation_rules is None:
            return specified_rules
        return self.validation_rules

    @staticmethod
    async def parse_body(request):
        content_type = request.content_type
        # request.text() is the aiohttp equivalent to
        # request.body.decode("utf8")
        if content_type == "application/graphql":
            r_text = await request.text()
            return {"query": r_text}

        if content_type == "application/json":
            text = await request.text()
            return load_json_body(text)

        if content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            # TODO: seems like a multidict would be more appropriate
            #  than casting it and de-duping variables. Alas, it's what
            #  graphql-python wants.
            return dict(await request.post())

        return {}

    def is_graphiql(self, request_method, is_raw, accept_headers):
        return (self.graphiql and request_method == "get"
                and not is_raw and ("text/html" in accept_headers or "*/*" in accept_headers),
        )

    def should_prettify(self, is_graphiql, pretty_query):
        return self.pretty or is_graphiql or pretty_query

    async def __call__(self, request):
        try:
            data = await self.parse_body(request)
            request_method = request.method.lower()
            accept_headers = request.headers.get("accept", {})
            is_graphiql = self.is_graphiql(request_method, request.query.get("raw"), accept_headers)
            is_pretty = self.should_prettify(is_graphiql, request.query.get("pretty"))

            if request_method == "options":
                headers = request.headers
                origin = headers.get("Origin", "")
                method = headers.get("Access-Control-Request-Method", "").upper()
                response = process_preflight(origin, method, self.accepted_methods, self.max_age)
                return web.Response(
                    status=response.status_code,
                    headers = response.headers
                )

            graphql_response = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=request.query,
                batch_enabled=self.batch,
                catch=is_graphiql,
                # Execute options
                run_sync=not self.enable_async,
                root_value=self.get_root_value(),
                context_value=self.get_context(request),
                middleware=self.get_middleware(),
                validation_rules=self.get_validation_rules(),
            )

            exec_res = (
                [
                    ex if ex is None or isinstance(ex, ExecutionResult) else await ex
                    for ex in graphql_response.results
                ]
                if self.enable_async
                else graphql_response.results
            )
            response = encode_execution_results(
                exec_res,
                is_batch=isinstance(data, list),
                format_error=self.format_error,
                encode=partial(self.encode, pretty=is_pretty),  # noqa: ignore
            )

            if is_graphiql:
                source = self.render_graphiql(
                    result=response.body,
                    params=graphql_response.all_params[0],
                    options=self.graphiql_options
                )
                return web.Response(text=source, content_type="text/html")

            return web.Response(
                text=response.result,
                status=response.status_code,
                content_type="application/json",
            )

        except HttpQueryError as err:
            parsed_error = GraphQLError(err.message)
            return web.Response(
                body=self.encode(dict(errors=[self.format_error(parsed_error)])),
                status=err.status_code,
                headers=err.headers,
                content_type="application/json",
            )

    @classmethod
    def attach(cls, app, *, route_path="/graphql", route_name="graphql", **kwargs):
        view = cls(**kwargs)
        app.router.add_route("*", route_path, _asyncify(view), name=route_name)


def _asyncify(handler):
    """Return an async version of the given handler.

    This is mainly here because ``aiohttp`` can't infer the async definition of
    :py:meth:`.GraphQLView.__call__` and raises a :py:class:`DeprecationWarning`
    in tests. Wrapping it into an async function avoids the noisy warning.
    """

    async def _dispatch(request):
        return await handler(request)

    return _dispatch
