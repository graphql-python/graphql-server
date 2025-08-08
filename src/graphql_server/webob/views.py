from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from graphql_server.http import GraphQLRequestData
from graphql_server.http.exceptions import HTTPException
from graphql_server.http.sync_base_view import SyncBaseHTTPView, SyncHTTPRequestAdapter
from graphql_server.http.types import HTTPMethod, QueryParams
from graphql_server.http.typevars import Context, RootValue
from webob import Request, Response

if TYPE_CHECKING:
    from graphql.type import GraphQLSchema

    from graphql_server.http import GraphQLHTTPResponse
    from graphql_server.http.ides import GraphQL_IDE


class WebobHTTPRequestAdapter(SyncHTTPRequestAdapter):
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return dict(self.request.GET.items())

    @property
    def body(self) -> Union[str, bytes]:
        return self.request.body

    @property
    def method(self) -> HTTPMethod:
        return cast("HTTPMethod", self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def post_data(self) -> Mapping[str, Union[str, bytes]]:
        return self.request.POST

    @property
    def files(self) -> Mapping[str, Any]:
        return {
            name: value.file
            for name, value in self.request.POST.items()
            if hasattr(value, "file")
        }

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type


class GraphQLView(
    SyncBaseHTTPView[Request, Response, Response, Context, RootValue],
):
    allow_queries_via_get: bool = True
    request_adapter_class = WebobHTTPRequestAdapter

    def __init__(
        self,
        schema: GraphQLSchema,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.multipart_uploads_enabled = multipart_uploads_enabled

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

    def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}  # type: ignore

    def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")

    def create_response(
        self,
        response_data: GraphQLHTTPResponse,
        sub_response: Response,
        is_strict: bool,
    ) -> Response:
        sub_response.text = self.encode_json(response_data)
        sub_response.content_type = (
            "application/graphql-response+json" if is_strict else "application/json"
        )
        return sub_response

    def render_graphql_ide(
        self, request: Request, request_data: GraphQLRequestData
    ) -> Response:
        return Response(
            text=request_data.to_template_string(self.graphql_ide_html),
            content_type="text/html",
            status=200,
        )

    def dispatch_request(self, request: Request) -> Response:
        try:
            return self.run(request=request)
        except HTTPException as e:
            return Response(text=e.reason, status=e.status_code)


__all__ = ["GraphQLView"]
