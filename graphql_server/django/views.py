import asyncio
import re
from functools import partial
from http.client import HTTPResponse
from typing import Type, Any, Optional, Collection

from graphql import ExecutionResult, GraphQLError, specified_rules
from graphql.execution import Middleware
from graphql.type.schema import GraphQLSchema
from graphql.validation import ASTValidationRule
from django.views.generic import View
from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest
from django.utils.decorators import classonlymethod, method_decorator
from django.views.decorators.csrf import csrf_exempt

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


def get_accepted_content_types(request):
    def qualify(x):
        parts = x.split(";", 1)
        if len(parts) == 2:
            match = re.match(r"(^|;)q=(0(\.\d{,3})?|1(\.0{,3})?)(;|$)", parts[1])
            if match:
                return parts[0].strip(), float(match.group(2))
        return parts[0].strip(), 1

    raw_content_types = request.META.get("HTTP_ACCEPT", "*/*").split(",")
    qualified_content_types = map(qualify, raw_content_types)
    return list(
        x[0] for x in sorted(qualified_content_types, key=lambda x: x[1], reverse=True)
    )


class GraphQLView(View):

    accepted_methods = ["GET", "POST", "PUT", "DELETE"]

    format_error = staticmethod(format_error_default)
    encode = staticmethod(json_encode)

    schema: GraphQLSchema = None
    root_value: Any = None
    pretty: bool = False
    graphiql: bool = True
    middleware: Optional[Middleware] = None
    validation_rules: Optional[Collection[Type[ASTValidationRule]]] = None
    batch: bool = False
    fetch_query_on_load: bool = True
    max_age: int = 86400
    graphiql_options: Optional[GraphiQLOptions] = None

    def __init__(
        self,
        schema: GraphQLSchema,
        root_value: Any = None,
        pretty: bool = False,
        graphiql: bool = True,
        middleware: Optional[Middleware] = None,
        validation_rules: Optional[Collection[Type[ASTValidationRule]]] = None,
        batch: bool = False,
        fetch_query_on_load: bool = True,
        max_age: int = 86400,
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
        self.fetch_query_on_load = fetch_query_on_load
        self.max_age = max_age

    def render_graphiql(self, *args, **kwargs):
        return render_graphiql_sync(*args, **kwargs)

    def get_root_value(self, request: HttpRequest):
        return self.root_value

    def get_context(self, request: HttpRequest):
        return request

    def get_middleware(self):
        return self.middleware

    def get_validation_rules(self):
        if self.validation_rules is None:
            return specified_rules
        return self.validation_rules

    def parse_body(self, request: HttpRequest):
        content_type = request.content_type

        if content_type == "application/graphql":
            return {"query": request.body.decode()}

        elif content_type == "application/json":
            try:
                body = request.body.decode("utf-8")
            except Exception as e:
                raise HttpQueryError(400, str(e))

            return load_json_body(body, self.batch)

        elif content_type in [
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]:
            return request.POST

        return {}

    @classmethod
    def request_prefers_html(cls, request: HttpRequest):
        accepted = get_accepted_content_types(request)
        accepted_length = len(accepted)
        # the list will be ordered in preferred first - so we have to make
        # sure the most preferred gets the highest number
        html_priority = (
            accepted_length - accepted.index("text/html")
            if "text/html" in accepted
            else 0
        )
        json_priority = (
            accepted_length - accepted.index("application/json")
            if "application/json" in accepted
            else 0
        )

        return html_priority > json_priority

    def is_graphiql(self, request_method: str, is_raw: bool, prefers_html: bool):
        return self.graphiql and request_method == "get" and not is_raw and prefers_html

    def should_prettify(self, is_graphiql: bool, pretty_in_query: bool):
        return self.pretty or is_graphiql or pretty_in_query

    @method_decorator(csrf_exempt)
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        try:
            data = self.parse_body(request)
            request_method = request.method.lower()
            prefers_html = self.request_prefers_html(request)
            is_graphiql = self.is_graphiql(
                request_method, "raw" in request.GET, prefers_html
            )
            is_pretty = self.should_prettify(is_graphiql, request.GET.get("pretty"))

            if request_method == "options":
                headers = request.headers
                origin = headers.get("Origin", "")
                method = headers.get("Access-Control-Request-Method", "").upper()
                response = process_preflight(
                    origin, method, self.accepted_methods, self.max_age
                )
                return HTTPResponse(
                    status=response.status_code, headers=response.headers
                )

            graphql_response = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=request.GET,
                batch_enabled=self.batch,
                catch=is_graphiql,
                # Execute options
                run_sync=True,
                root_value=self.get_root_value(request),
                context_value=self.get_context(request),
                middleware=self.get_middleware(),
                validation_rules=self.get_validation_rules(),
            )

            response = encode_execution_results(
                graphql_response.results,
                is_batch=isinstance(data, list),
                format_error=self.format_error,
                encode=partial(self.encode, pretty=is_pretty),  # noqa: ignore
            )

            if is_graphiql:
                source = self.render_graphiql(
                    result=response.body,
                    params=graphql_response.params[0],
                    options=self.graphiql_options,
                )
                return HttpResponse(content=source, content_type="text/html")

            return HttpResponse(
                content=response.body,
                content_type="application/json",
                status=response.status_code,
            )

        except HttpQueryError as err:
            parsed_error = GraphQLError(err.message)
            return HttpResponse(
                content=self.encode(dict(errors=[self.format_error(parsed_error)])),
                content_type="application/json",
                status=err.status_code,
                headers=err.headers,
            )


class AsyncGraphQLView(GraphQLView):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # This code tells django that this view is async, see docs here:
        # https://docs.djangoproject.com/en/3.1/topics/async/#async-views

        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

    @method_decorator(csrf_exempt)
    async def dispatch(self, request, *args, **kwargs):
        try:
            data = self.parse_body(request)
            request_method = request.method.lower()
            prefers_html = self.request_prefers_html(request)
            is_graphiql = self.is_graphiql(
                request_method, "raw" in request.GET, prefers_html
            )
            is_pretty = self.should_prettify(is_graphiql, request.GET.get("pretty"))

            if request_method == "options":
                headers = request.headers
                origin = headers.get("Origin", "")
                method = headers.get("Access-Control-Request-Method", "").upper()
                response = process_preflight(
                    origin, method, self.accepted_methods, self.max_age
                )
                return HTTPResponse(
                    status=response.status_code, headers=response.headers
                )

            graphql_response = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=request.GET,
                batch_enabled=self.batch,
                catch=is_graphiql,
                # Execute options
                run_sync=False,
                root_value=await self.get_root_value(request),
                context_value=await self.get_context(request),
                middleware=self.get_middleware(),
                validation_rules=self.get_validation_rules(),
            )

            exec_res = [
                ex if ex is None or isinstance(ex, ExecutionResult) else await ex
                for ex in graphql_response.results
            ]

            response = encode_execution_results(
                exec_res,
                is_batch=isinstance(data, list),
                format_error=self.format_error,
                encode=partial(self.encode, pretty=is_pretty),  # noqa: ignore
            )

            if is_graphiql:
                source = self.render_graphiql(
                    result=response.body,
                    params=graphql_response.params[0],
                    options=self.graphiql_options,
                )
                return HttpResponse(content=source, content_type="text/html")

            return HttpResponse(
                content=response.body,
                content_type="application/json",
                status=response.status_code,
            )

        except HttpQueryError as err:
            parsed_error = GraphQLError(err.message)
            return HttpResponse(
                content=self.encode(dict(errors=[self.format_error(parsed_error)])),
                content_type="application/json",
                status=err.status_code,
                headers=err.headers,
            )

    async def get_root_value(self, request: HttpRequest) -> Any:
        return None

    async def get_context(self, request: HttpRequest) -> Any:
        return request
