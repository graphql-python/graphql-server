from __future__ import annotations

import warnings
from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from chalice.app import Request, Response
from graphql_server.http import GraphQLRequestData
from graphql_server.http.exceptions import HTTPException
from graphql_server.http.sync_base_view import SyncBaseHTTPView, SyncHTTPRequestAdapter
from graphql_server.http.temporal_response import TemporalResponse
from graphql_server.http.typevars import Context, RootValue

if TYPE_CHECKING:
    from collections.abc import Mapping

    from graphql.type import GraphQLSchema

    from graphql_server.http import GraphQLHTTPResponse
    from graphql_server.http.ides import GraphQL_IDE
    from graphql_server.http.types import HTTPMethod, QueryParams


class ChaliceHTTPRequestAdapter(SyncHTTPRequestAdapter):
    def __init__(self, request: Request) -> None:
        self.request = request
        self._post_data: Optional[dict[str, Union[str, bytes]]] = None
        self._files: Optional[dict[str, Any]] = None

    @property
    def query_params(self) -> QueryParams:
        return self.request.query_params or {}

    @property
    def body(self) -> Union[str, bytes]:
        return self.request.raw_body

    @property
    def method(self) -> HTTPMethod:
        return cast("HTTPMethod", self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def post_data(self) -> Mapping[str, Union[str, bytes]]:
        if self._post_data is None:
            self._parse_body()
        return self._post_data or {}

    @property
    def files(self) -> Mapping[str, Any]:
        if self._files is None:
            self._parse_body()
        return self._files or {}

    def _parse_body(self) -> None:
        self._post_data = {}
        self._files = {}

        content_type = self.content_type or ""

        if "multipart/form-data" in content_type:
            import cgi

            fp = BytesIO(self.request.raw_body)
            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(len(self.request.raw_body)),
            }
            fs = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)
            for key in fs.keys():
                field = fs[key]
                if isinstance(field, list):
                    field = field[0]
                if getattr(field, "filename", None):
                    data = field.file.read()
                    self._files[key] = BytesIO(data)
                else:
                    self._post_data[key] = field.value
        elif "application/x-www-form-urlencoded" in content_type:
            from urllib.parse import parse_qs

            data = parse_qs(self.request.raw_body.decode())
            self._post_data = {k: v[0] for k, v in data.items()}
        else:
            self._post_data = {}
            self._files = {}

    @property
    def content_type(self) -> Optional[str]:
        return self.request.headers.get("Content-Type", None)


class GraphQLView(
    SyncBaseHTTPView[Request, Response, TemporalResponse, Context, RootValue]
):
    allow_queries_via_get: bool = True
    request_adapter_class = ChaliceHTTPRequestAdapter

    def __init__(
        self,
        schema: GraphQLSchema,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.allow_queries_via_get = allow_queries_via_get
        self.schema = schema
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

    def render_graphql_ide(
        self, request: Request, request_data: GraphQLRequestData
    ) -> Response:
        return Response(
            request_data.to_template_string(self.graphql_ide_html),
            headers={"Content-Type": "text/html"},
        )

    def get_sub_response(self, request: Request) -> TemporalResponse:
        return TemporalResponse()

    @staticmethod
    def error_response(
        message: str,
        http_status_code: int,
        headers: Optional[dict[str, str | list[str]]] = None,
    ) -> Response:
        """A wrapper for error responses.

        Args:
            message: The error message.
            error_code: The error code.
            http_status_code: The HTTP status code.
            headers: The headers to include in the response.

        Returns:
            An errors response.
        """
        return Response(body=message, status_code=http_status_code, headers=headers)

    def get_context(self, request: Request, response: TemporalResponse) -> Context:
        return {"request": request, "response": response}  # type: ignore

    def create_response(
        self,
        response_data: GraphQLHTTPResponse,
        sub_response: TemporalResponse,
        is_strict: bool,
    ) -> Response:
        return Response(
            body=self.encode_json(response_data),
            status_code=sub_response.status_code,
            headers={
                "Content-Type": "application/graphql-response+json"
                if is_strict
                else "application/json",
                **sub_response.headers,
            },
        )

    def execute_request(self, request: Request) -> Response:
        try:
            return self.run(request=request)
        except HTTPException as e:
            return self.error_response(
                message=e.reason,
                http_status_code=e.status_code,
            )


__all__ = ["GraphQLView"]
