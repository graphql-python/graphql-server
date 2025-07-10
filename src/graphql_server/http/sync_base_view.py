import abc
import json
from collections.abc import Mapping
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Optional,
    Union,
)

from graphql import ExecutionResult, GraphQLError
from graphql.language import OperationType
from graphql.type import GraphQLSchema

from graphql_server import execute_sync
from graphql_server.exceptions import GraphQLValidationError, InvalidOperationTypeError
from graphql_server.file_uploads.utils import replace_placeholders_with_files
from graphql_server.http import (
    GraphQLHTTPResponse,
    GraphQLRequestData,
    process_result,
)
from graphql_server.http.ides import GraphQL_IDE
from graphql_server.http.types import operation_type_from_http
from graphql_server.types.unset import UNSET

from .base import BaseView
from .exceptions import HTTPException
from .parse_content_type import parse_content_type
from .types import HTTPMethod, QueryParams
from .typevars import Context, Request, Response, RootValue, SubResponse


class SyncHTTPRequestAdapter(abc.ABC):
    @property
    @abc.abstractmethod
    def query_params(self) -> QueryParams: ...

    @property
    @abc.abstractmethod
    def body(self) -> Union[str, bytes]: ...

    @property
    @abc.abstractmethod
    def method(self) -> HTTPMethod: ...

    @property
    @abc.abstractmethod
    def headers(self) -> Mapping[str, str]: ...

    @property
    @abc.abstractmethod
    def content_type(self) -> Optional[str]: ...

    @property
    @abc.abstractmethod
    def post_data(self) -> Mapping[str, Union[str, bytes]]: ...

    @property
    @abc.abstractmethod
    def files(self) -> Mapping[str, Any]: ...


class SyncBaseHTTPView(
    abc.ABC,
    BaseView[Request],
    Generic[Request, Response, SubResponse, Context, RootValue],
):
    schema: GraphQLSchema
    graphiql: Optional[bool]
    graphql_ide: Optional[GraphQL_IDE]
    request_adapter_class: Callable[[Request], SyncHTTPRequestAdapter]

    # Methods that need to be implemented by individual frameworks

    @property
    @abc.abstractmethod
    def allow_queries_via_get(self) -> bool: ...

    @abc.abstractmethod
    def get_sub_response(self, request: Request) -> SubResponse: ...

    @abc.abstractmethod
    def get_context(self, request: Request, response: SubResponse) -> Context: ...

    @abc.abstractmethod
    def get_root_value(self, request: Request) -> Optional[RootValue]: ...

    @abc.abstractmethod
    def create_response(
        self,
        response_data: GraphQLHTTPResponse,
        sub_response: SubResponse,
        is_strict: bool,
    ) -> Response: ...

    @abc.abstractmethod
    def render_graphql_ide(
        self, request: Request, request_data: GraphQLRequestData
    ) -> Response: ...

    def execute_operation(
        self,
        request_adapter: SyncHTTPRequestAdapter,
        request_data: GraphQLRequestData,
        context: Context,
        root_value: Optional[RootValue],
        allowed_operation_types: set[OperationType],
    ) -> ExecutionResult:
        assert self.schema

        return execute_sync(
            schema=self.schema,
            query=request_data.document or request_data.query,
            root_value=root_value,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
            allowed_operation_types=allowed_operation_types,
            operation_extensions=request_data.extensions,
        )

    def parse_multipart(self, request: SyncHTTPRequestAdapter) -> dict[str, str]:
        operations = self.parse_json(request.post_data.get("operations", "{}"))
        files_map = self.parse_json(request.post_data.get("map", "{}"))

        try:
            return replace_placeholders_with_files(operations, files_map, request.files)
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

    def get_graphql_request_data(
        self,
        request: SyncHTTPRequestAdapter,
        context: Context,
        data: dict[str, Any],
        protocol: Literal["http", "http-strict", "multipart-subscription"],
    ) -> GraphQLRequestData:
        return GraphQLRequestData(
            query=data.get("query"),
            document=None,
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
            extensions=data.get("extensions"),
            protocol=protocol,
        )

    def parse_http_body(
        self,
        request: SyncHTTPRequestAdapter,
        context: Context,
    ) -> GraphQLRequestData:
        accept_type = request.headers.get("accept", "") or request.headers.get(
            "http-accept", ""
        )
        content_type, params = parse_content_type(request.content_type or "")

        protocol = "http"
        if "application/graphql-response+json" in accept_type:
            protocol = "http-strict"

        if request.method == "GET":
            data = self.parse_query_params(request.query_params)
        elif "application/json" in content_type:
            data = self.parse_json(request.body)
        # TODO: multipart via get?
        elif self.multipart_uploads_enabled and content_type == "multipart/form-data":
            data = self.parse_multipart(request)
        elif self._is_multipart_subscriptions(content_type, params):
            raise HTTPException(
                400, "Multipart subscriptions are not supported in sync mode"
            )
        else:
            raise HTTPException(400, "Unsupported content type")

        return self.get_graphql_request_data(request, context, data, protocol)

    def _handle_errors(
        self, errors: list[GraphQLError], response_data: GraphQLHTTPResponse
    ) -> None:
        """Hook to allow custom handling of errors, used by the Sentry Integration."""

    def run(
        self,
        request: Request,
        context: Context = UNSET,
        root_value: Optional[RootValue] = UNSET,
    ) -> Response:
        request_adapter = self.request_adapter_class(request)
        if request_adapter.method == "OPTIONS":
            # We are in a CORS preflight request, we can return a 200 OK by default
            # as further checks will need to be done by the middleware
            raise HTTPException(200, "")

        if not self.is_request_allowed(request_adapter):
            raise HTTPException(405, "GraphQL only supports GET and POST requests.")

        sub_response = self.get_sub_response(request)
        context = (
            self.get_context(request, response=sub_response)
            if context is UNSET
            else context
        )

        try:
            request_data = self.parse_http_body(request_adapter, context)
        except json.decoder.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e
            # DO this only when doing files
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

        if request_data.variables is not None and not isinstance(
            request_data.variables, dict
        ):
            raise HTTPException(400, "Variables must be a JSON object")

        if request_data.extensions is not None and not isinstance(
            request_data.extensions, dict
        ):
            raise HTTPException(400, "Extensions must be a JSON object")

        allowed_operation_types = operation_type_from_http(request_adapter.method)

        if request_adapter.method == "GET":
            if not self.allow_queries_via_get:
                allowed_operation_types = allowed_operation_types - {
                    OperationType.QUERY
                }

            if self.graphql_ide and self.should_render_graphql_ide(request_adapter):
                return self.render_graphql_ide(request, request_data)

        root_value = self.get_root_value(request) if root_value is UNSET else root_value
        is_strict = request_data.protocol == "http-strict"
        try:
            result = self.execute_operation(
                request_adapter=request_adapter,
                request_data=request_data,
                context=context,
                root_value=root_value,
                allowed_operation_types=allowed_operation_types,
            )
        except HTTPException:
            raise
        except GraphQLValidationError as e:
            if is_strict:
                sub_response.status_code = 400  # type: ignore
            result = ExecutionResult(data=None, errors=e.errors)
        except InvalidOperationTypeError as e:
            raise HTTPException(
                400, e.as_http_error_reason(request_adapter.method)
            ) from e
        except Exception as e:
            raise HTTPException(400, str(e)) from e

        response_data = self.process_result(
            request=request, result=result, strict=is_strict
        )

        if result.errors:
            self._handle_errors(result.errors, response_data)

        return self.create_response(
            response_data=response_data, sub_response=sub_response, is_strict=is_strict
        )

    def process_result(
        self, request: Request, result: ExecutionResult, strict: bool = False
    ) -> GraphQLHTTPResponse:
        return process_result(result, strict)


__all__ = ["SyncBaseHTTPView"]
