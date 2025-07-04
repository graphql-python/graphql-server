from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional
from typing_extensions import Literal, TypedDict

from graphql.language import DocumentNode

if TYPE_CHECKING:
    from graphql import ExecutionResult


class GraphQLHTTPResponse(TypedDict, total=False):
    data: Optional[dict[str, object]]
    errors: Optional[list[object]]
    extensions: Optional[dict[str, object]]


def process_result(
    result: ExecutionResult, strict: bool = False
) -> GraphQLHTTPResponse:
    if strict and not result.data:
        data: GraphQLHTTPResponse = {}
    else:
        data: GraphQLHTTPResponse = {"data": result.data}

    if result.errors:
        data["errors"] = [err.formatted for err in result.errors]
    if result.extensions:
        data["extensions"] = result.extensions

    return data


def tojson(value):
    if value not in ["true", "false", "null", "undefined"]:
        value = json.dumps(value)
        # value = escape_js_value(value)
    return value


def simple_renderer(template: str, **values: str) -> str:
    def get_var(match_obj: re.Match[str]) -> str:
        var_name = match_obj.group(1)
        if var_name is not None:
            return values.get(var_name) or tojson("")
        return ""

    pattern = r"{{\s*([^}]+)\s*}}"
    return re.sub(pattern, get_var, template)


@dataclass
class GraphQLRequestData:
    # query is optional here as it can be added by an extensions
    # (for example an extension for persisted queries)
    query: Optional[str]
    document: Optional[DocumentNode]
    variables: Optional[dict[str, Any]]
    operation_name: Optional[str]
    extensions: Optional[dict[str, Any]]
    protocol: Literal[
        "http", "http-strict", "multipart-subscription", "subscription"
    ] = "http"

    def to_template_context(self) -> dict[str, Any]:
        return {
            "query": tojson(self.query),
            "variables": tojson(
                tojson(self.variables) if self.variables is not None else ""
            ),
            "operation_name": tojson(self.operation_name),
        }

    def to_template_string(self, template: str) -> str:
        return simple_renderer(template, **self.to_template_context())


__all__ = [
    "GraphQLHTTPResponse",
    "GraphQLRequestData",
    "process_result",
]
