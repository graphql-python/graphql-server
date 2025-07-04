from __future__ import annotations

import asyncio
import contextvars
import functools
import json
import urllib.parse
from io import BytesIO
from typing import Any, Optional, Union
from typing_extensions import Literal

from graphql import ExecutionResult
from webob import Request, Response

from graphql_server.http import GraphQLHTTPResponse
from graphql_server.http.ides import GraphQL_IDE
from graphql_server.webob import GraphQLView as BaseGraphQLView
from tests.http.context import get_context
from tests.views.schema import Query, schema

from .base import JSON, HttpClient, Response as ClientResponse, ResultOverrideFunction


class GraphQLView(BaseGraphQLView[dict[str, object], object]):
    result_override: ResultOverrideFunction = None

    def get_root_value(self, request: Request) -> Query:
        super().get_root_value(request)  # for coverage
        return Query()

    def get_context(self, request: Request, response: Response) -> dict[str, object]:
        context = super().get_context(request, response)
        return get_context(context)

    def process_result(
        self, request: Request, result: ExecutionResult, strict: bool = False
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)
        return super().process_result(request, result, strict)


class WebobHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.view = GraphQLView(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )
        self.view.result_override = result_override

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        operation_name: Optional[str] = None,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
        extensions: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ClientResponse:
        body = self._build_body(
            query=query,
            operation_name=operation_name,
            variables=variables,
            files=files,
            method=method,
            extensions=extensions,
        )

        data: Union[dict[str, object], str, None] = None

        url = "/graphql"

        if body and files:
            body.update({name: (file, name) for name, file in files.items()})

        if method == "get":
            body_encoded = urllib.parse.urlencode(body or {})
            url = f"{url}?{body_encoded}"
        else:
            if body:
                data = body if files else json.dumps(body)
            kwargs["body"] = data

        headers = self._get_headers(method=method, headers=headers, files=files)

        return await self.request(url, method, headers=headers, **kwargs)

    def _do_request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> ClientResponse:
        body = kwargs.get("body", None)
        req = Request.blank(
            url, method=method.upper(), headers=headers or {}, body=body
        )
        resp = self.view.dispatch_request(req)
        return ClientResponse(
            status_code=resp.status_code, data=resp.body, headers=resp.headers
        )

    async def request(
        self,
        url: str,
        method: Literal["head", "get", "post", "patch", "put", "delete"],
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> ClientResponse:
        loop = asyncio.get_running_loop()
        ctx = contextvars.copy_context()
        func_call = functools.partial(
            ctx.run, self._do_request, url=url, method=method, headers=headers, **kwargs
        )
        return await loop.run_in_executor(None, func_call)  # type: ignore

    async def get(
        self, url: str, headers: Optional[dict[str, str]] = None
    ) -> ClientResponse:
        return await self.request(url, "get", headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> ClientResponse:
        body = json if json is not None else data
        return await self.request(url, "post", headers=headers, body=body)
