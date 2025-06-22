from collections.abc import Mapping
from typing import Any, Optional
from typing_extensions import Literal, TypedDict

from graphql.language import OperationType

HTTPMethod = Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"
]

QueryParams = Mapping[str, Optional[str]]


class FormData(TypedDict):
    files: Mapping[str, Any]
    form: Mapping[str, Any]


def operation_type_from_http(method: HTTPMethod) -> set[OperationType]:
    if method == "GET":
        return {
            OperationType.QUERY,
            # subscriptions are supported via GET in the multipart protocol
            OperationType.SUBSCRIPTION,
        }

    if method == "POST":
        return {
            OperationType.QUERY,
            OperationType.MUTATION,
            OperationType.SUBSCRIPTION,
        }

    raise ValueError(f"Unsupported HTTP method: {method}")  # pragma: no cover


__all__ = ["FormData", "HTTPMethod", "QueryParams"]
