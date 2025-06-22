from typing import Set

from graphql import GraphQLError, OperationType


class GraphQLValidationError(GraphQLError):
    errors: list[GraphQLError]

    def __init__(self, errors: list[GraphQLError]):
        self.errors = errors
        super().__init__("Validation failed")


class InvalidOperationTypeError(GraphQLError):
    def __init__(
        self, operation_type: OperationType, allowed_operation_types: Set[OperationType]
    ) -> None:
        message = f"{self.format_operation_type(operation_type)} are not allowed."
        if allowed_operation_types:
            message += f" Only {', '.join(map(self.format_operation_type, allowed_operation_types))} are allowed."
        self.operation_type = operation_type
        super().__init__(message)

    def format_operation_type(self, operation_type: OperationType) -> str:
        return {
            OperationType.QUERY: "queries",
            OperationType.MUTATION: "mutations",
            OperationType.SUBSCRIPTION: "subscriptions",
        }[operation_type]

    def as_http_error_reason(self, method: str) -> str:
        return f"{self.format_operation_type(self.operation_type)} are not allowed when using {method}"


class ConnectionRejectionError(Exception):
    """Use it when you want to reject a WebSocket connection."""

    def __init__(self, payload: dict[str, object] | None = None) -> None:
        if payload is None:
            payload = {}
        self.payload = payload


__all__: list[str] = ["ConnectionRejectionError", "InvalidOperationTypeError"]
