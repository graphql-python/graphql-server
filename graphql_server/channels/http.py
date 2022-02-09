"""GraphQLHttpConsumer
A consumer to provide a graphql endpoint, and optionally graphiql.
"""
import re
from functools import partial
from urllib.parse import parse_qsl
from typing import Type, Any, Optional, Collection

from graphql import ExecutionResult, GraphQLError, specified_rules
from graphql.execution import Middleware
from graphql.type.schema import GraphQLSchema
from graphql.validation import ASTValidationRule
from channels.generic.http import AsyncHttpConsumer

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


def get_accepted_content_types(accept_header: str):
    def qualify(x):
        parts = x.split(";", 1)
        if len(parts) == 2:
            match = re.match(r"(^|;)q=(0(\.\d{,3})?|1(\.0{,3})?)(;|$)", parts[1])
            if match:
                return parts[0].strip(), float(match.group(2))
        return parts[0].strip(), 1

    raw_content_types = accept_header.split(",")
    qualified_content_types = map(qualify, raw_content_types)
    return list(
        x[0] for x in sorted(qualified_content_types, key=lambda x: x[1], reverse=True)
    )


class GraphQLHttpConsumer(AsyncHttpConsumer):
    def __init__(
        self,
        schema: GraphQLSchema,
        graphiql: bool = True,
    ):
        self.schema = schema
        self.graphiql = graphiql
        super().__init__()

    @property
    def headers(self):
        return {
            header_name.decode("utf-8").lower(): header_value.decode("utf-8")
            for header_name, header_value in self.scope["headers"]
        }

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
    cors_allow_origin: Optional[str] = None
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
        cors_allow_origin: Optional[str] = None,
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
        self.cors_allow_origin = cors_allow_origin
        self.max_age = max_age
        super().__init__()

    def render_graphiql(self, *args, **kwargs):
        return render_graphiql_sync(*args, **kwargs)

    async def get_root_value(self, request) -> Any:
        return None

    async def get_context(self, request) -> Any:
        return None

    def get_middleware(self):
        return self.middleware

    def get_validation_rules(self):
        if self.validation_rules is None:
            return specified_rules
        return self.validation_rules

    def parse_body(self, content_type, body):
        if content_type == "application/graphql":
            return {"query": body.decode()}

        elif content_type == "application/json":
            try:
                body = body.decode("utf-8")
            except Exception as e:
                raise HttpQueryError(400, str(e))

            return load_json_body(body, self.batch)

        elif content_type in [
            "application/x-www-form-urlencoded",
            # "multipart/form-data",
        ]:
            return dict(parse_qsl(body.decode("utf-8")))

        return {}

    def request_prefers_html(self, accept):

        accepted = get_accepted_content_types(accept)
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

    async def handle(self, body):
        if self.cors_allow_origin:
            base_cors_headers = [
                (b"Access-Control-Allow-Origin", self.cors_allow_origin)
            ]
        else:
            base_cors_headers = []
        try:
            req_headers = self.headers
            content_type = req_headers.get("content-type", "")
            accept_header = req_headers.get("accept", "*/*")
            data = self.parse_body(content_type, body)
            request_method = self.scope["method"].lower()
            prefers_html = self.request_prefers_html(accept_header) or True
            query_data = dict(parse_qsl(self.scope.get("query_string", b"").decode("utf-8")))
            is_raw = "raw" in query_data
            is_pretty = "pretty" in query_data
            is_pretty = False
            is_graphiql = self.is_graphiql(request_method, is_raw, prefers_html)
            is_pretty = self.should_prettify(is_graphiql, is_pretty)

            if request_method == "options":
                origin = req_headers.get("origin", "")
                method = req_headers.get("access-control-request-method", "").upper()
                response = process_preflight(
                    origin, method, self.accepted_methods, self.max_age
                )
                headers = [
                    (b"Content-Type", b"application/json"),
                    (b"Access-Control-Allow-Headers", b"*"),
                ]
                if response.headers:
                    headers += [
                        (key.encode("utf-8"), value.encode("utf-8"))
                        for key, value in response.headers.items()
                    ]
                else:
                    headers = []
                await self.send_response(response.status_code, b"{}", headers=headers)
                return

            graphql_response = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=query_data,
                batch_enabled=self.batch,
                catch=is_graphiql,
                # Execute options
                run_sync=False,
                root_value=await self.get_root_value(self),
                context_value=await self.get_context(self),
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
                await self.send_response(
                    200,
                    source.encode("utf-8"),
                    headers=base_cors_headers + [(b"Content-Type", b"text/html")],
                )
                return

            await self.send_response(
                response.status_code,
                response.body.encode("utf-8"),
                headers=base_cors_headers + [(b"Content-Type", b"application/json")],
            )
            return

        except HttpQueryError as err:
            parsed_error = GraphQLError(err.message)
            data = self.encode(dict(errors=[self.format_error(parsed_error)]))
            headers = [(b"Content-Type", b"application/json")]
            if err.headers:
                headers = headers + [(key, value) for key, value in err.headers.items()]
            await self.send_response(
                err.status_code,
                data.encode("utf-8"),
                headers=base_cors_headers + headers,
            )
            return
        except Exception as e:
            parsed_error = GraphQLError(str(e))
            data = self.encode(dict(errors=[self.format_error(parsed_error)]))
            headers = [(b"Content-Type", b"application/json")]
            await self.send_response(
                400,
                data.encode("utf-8"),
                headers=headers,
            )
            return
