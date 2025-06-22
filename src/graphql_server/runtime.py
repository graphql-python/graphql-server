from __future__ import annotations

import warnings
from asyncio import ensure_future
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Iterable
from functools import cached_property, lru_cache
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    NamedTuple,
    Optional,
    Set,
    Union,
    cast,
)

from graphql import (
    ExecutionContext,
    ExecutionResult,
    FieldNode,
    FragmentDefinitionNode,
    GraphQLBoolean,
    GraphQLError,
    GraphQLField,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLSchema,
    OperationDefinitionNode,
    get_introspection_query,
    parse,
    print_schema,
    validate_schema,
)
from graphql.error import GraphQLError
from graphql.execution import execute as graphql_execute
from graphql.execution import execute_sync as graphql_execute_sync
from graphql.execution import subscribe as graphql_subscribe
from graphql.execution.middleware import MiddlewareManager
from graphql.language import OperationType
from graphql.type import GraphQLSchema
from graphql.type.directives import specified_directives
from graphql.validation import validate

from graphql_server.exceptions import GraphQLValidationError, InvalidOperationTypeError
from graphql_server.utils import IS_GQL_32, IS_GQL_33
from graphql_server.utils.aio import aclosing
from graphql_server.utils.await_maybe import await_maybe
from graphql_server.utils.logs import GraphQLServerLogger

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from typing_extensions import TypeAlias

    from graphql.execution.collect_fields import FieldGroup  # type: ignore
    from graphql.language import DocumentNode
    from graphql.pyutils import Path
    from graphql.type import GraphQLResolveInfo
    from graphql.validation import ASTValidationRule

SubscriptionResult: TypeAlias = AsyncGenerator[ExecutionResult, None]

OriginSubscriptionResult = Union[
    ExecutionResult,
    AsyncIterator[ExecutionResult],
]

DEFAULT_ALLOWED_OPERATION_TYPES = {
    OperationType.QUERY,
    OperationType.MUTATION,
    OperationType.SUBSCRIPTION,
}
ProcessErrors: TypeAlias = (
    "Callable[[list[GraphQLError], Optional[ExecutionContext]], None]"
)


def validate_document(
    schema: GraphQLSchema,
    document: DocumentNode,
    validation_rules: Optional[tuple[type[ASTValidationRule], ...]] = None,
) -> list[GraphQLError]:
    if validation_rules is not None:
        validation_rules = (*validation_rules,)
    return validate(
        schema,
        document,
        validation_rules,
    )


def _run_validation(
    schema: GraphQLSchema,
    graphql_document: DocumentNode,
    validation_rules: Optional[tuple[type[ASTValidationRule], ...]] = None,
) -> list[GraphQLError] | None:
    assert graphql_document, "GraphQL document is required for validation"
    errors = validate_document(
        schema,
        graphql_document,
        validation_rules,
    )
    if errors:
        raise GraphQLValidationError(errors)
    return None


def _coerce_error(error: Union[GraphQLError, Exception]) -> GraphQLError:
    if isinstance(error, GraphQLError):
        return error
    return GraphQLError(str(error), original_error=error)


def _get_custom_context_kwargs(
    operation_extensions: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if not IS_GQL_33:
        return {}

    return {"operation_extensions": operation_extensions}


def _get_operation_type(
    document: DocumentNode, operation_name: Optional[str] = None
) -> OperationType:
    if operation_name is not None:
        if not isinstance(operation_name, str):
            raise GraphQLError("Must provide a valid operation name.")

    operation: Optional[OperationType] = None
    for definition in document.definitions:
        if isinstance(definition, OperationDefinitionNode):
            if operation_name is None:
                if operation:
                    raise Exception(
                        "Must provide operation name"
                        " if query contains multiple operations."
                    )
                operation = definition.operation
            elif definition.name and definition.name.value == operation_name:
                operation = definition.operation
    if not operation:
        if operation_name is not None:
            raise GraphQLError(f'Unknown operation named "{operation_name}".')
        raise GraphQLError("Can't get GraphQL operation type")
    return operation


def _parse_and_validate(
    schema: GraphQLSchema,
    query: Union[Optional[str], DocumentNode],
    allowed_operation_types: Optional[Set[OperationType]],
    validation_rules: Optional[tuple[type[ASTValidationRule], ...]] = None,
    operation_name: Optional[str] = None,
    # extensions_runner: SchemaExtensionsRunner
) -> DocumentNode:
    if allowed_operation_types is None:
        allowed_operation_types = DEFAULT_ALLOWED_OPERATION_TYPES

    # async with extensions_runner.parsing():
    if not query:
        raise GraphQLError("No GraphQL query found in the request")

    try:
        if isinstance(query, str):
            document_node = parse(query)
        else:
            document_node = query
    except GraphQLError as e:
        raise GraphQLValidationError([e]) from e

    operation_type = _get_operation_type(document_node, operation_name)
    if operation_type not in allowed_operation_types:
        raise InvalidOperationTypeError(operation_type, allowed_operation_types)

    # async with extensions_runner.validation():
    _run_validation(schema, document_node, validation_rules)

    return document_node


def _handle_execution_result(
    result: ExecutionResult,
) -> ExecutionResult:
    # Set errors on the context so that it's easier
    # to access in extensions
    if result.errors:
        # if not skipprocess_errors:
        process_errors(result.errors)
    # result.extensions = await extensions_runner.get_extensions_results(context)
    return result


async def execute(
    schema: GraphQLSchema,
    query: Union[Optional[str], DocumentNode],
    variable_values: Optional[dict[str, Any]] = None,
    context_value: Optional[Any] = None,
    root_value: Optional[Any] = None,
    operation_name: Optional[str] = None,
    allowed_operation_types: Optional[Set[OperationType]] = None,
    operation_extensions: Optional[dict[str, Any]] = None,
    middleware: Optional[MiddlewareManager] = None,
    custom_context_kwargs: Optional[dict[str, Any]] = None,
    execution_context_class: type[ExecutionContext] | None = None,
    validation_rules: Optional[tuple[type[ASTValidationRule], ...]] = None,
) -> ExecutionResult:
    if allowed_operation_types is None:
        allowed_operation_types = DEFAULT_ALLOWED_OPERATION_TYPES
    if custom_context_kwargs is None:
        custom_context_kwargs = {}
    # extensions = self.get_extensions()
    # # TODO (#3571): remove this when we implement execution context as parameter.
    # for extension in extensions:
    #     extension.execution_context = execution_context

    # extensions_runner = self.create_extensions_runner(execution_context, extensions)

    try:
        # async with extensions_runner.operation():
        #     # Note: In graphql-core the schema would be validated here but
        #     # we are validating it at initialisation time instead

        graphql_document = _parse_and_validate(
            schema,
            query,
            allowed_operation_types,
            validation_rules,
            operation_name,
        )

        #     async with extensions_runner.executing():
        result = await await_maybe(
            graphql_execute(
                schema,
                graphql_document,
                root_value=root_value,
                middleware=middleware,
                variable_values=variable_values,
                operation_name=operation_name,
                context_value=context_value,
                execution_context_class=execution_context_class,
                **custom_context_kwargs,
            )
        )
    except GraphQLError:
        raise
    except Exception as exc:  # noqa: BLE001
        result = ExecutionResult(data=None, errors=[_coerce_error(exc)])
    # return results after all the operation completed.
    return _handle_execution_result(
        result,
        # extensions_runner,
    )


def execute_sync(
    schema: GraphQLSchema,
    query: Union[Optional[str], DocumentNode],
    variable_values: Optional[dict[str, Any]] = None,
    context_value: Optional[Any] = None,
    root_value: Optional[Any] = None,
    operation_name: Optional[str] = None,
    allowed_operation_types: Optional[Set[OperationType]] = None,
    operation_extensions: Optional[dict[str, Any]] = None,
    middleware: Optional[MiddlewareManager] = None,
    custom_context_kwargs: Optional[dict[str, Any]] = None,
    execution_context_class: type[ExecutionContext] | None = None,
    validation_rules: Optional[tuple[type[ASTValidationRule], ...]] = None,
) -> ExecutionResult:
    if custom_context_kwargs is None:
        custom_context_kwargs = {}

    # extensions = self._sync_extensions
    # # TODO (#3571): remove this when we implement execution context as parameter.
    # for extension in extensions:
    #     extension.execution_context = execution_context

    # extensions_runner = self.create_extensions_runner(execution_context, extensions)

    try:
        # with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but
        # we are validating it at initialisation time instead

        graphql_document = _parse_and_validate(
            schema,
            query,
            allowed_operation_types,
            validation_rules,
            operation_name,
        )

        # with extensions_runner.executing():
        result = graphql_execute_sync(
            schema,
            graphql_document,
            root_value=root_value,
            middleware=middleware,
            variable_values=variable_values,
            operation_name=operation_name,
            context_value=context_value,
            execution_context_class=execution_context_class,
            **custom_context_kwargs,
        )

        if isawaitable(result):
            result = cast("Awaitable[ExecutionResult]", result)  # type: ignore[redundant-cast]
            ensure_future(result).cancel()
            raise RuntimeError(  # noqa: TRY301
                "GraphQL execution failed to complete synchronously."
            )

        result = cast("ExecutionResult", result)  # type: ignore[redundant-cast]
    except GraphQLError:
        raise
    except Exception as exc:  # noqa: BLE001
        result = ExecutionResult(
            data=None,
            errors=[_coerce_error(exc)],
            # extensions=extensions_runner.get_extensions_results_sync(),
        )
    return _handle_execution_result(
        result,
        # extensions_runner,
    )


async def subscribe(
    schema: GraphQLSchema,
    query: Union[Optional[str], DocumentNode],
    root_value: Optional[Any] = None,
    variable_values: Optional[dict[str, Any]] = None,
    operation_name: Optional[str] = None,
    context_value: Optional[Any] = None,
    middleware_manager: Optional[MiddlewareManager] = None,
    execution_context_class: Optional[type[ExecutionContext]] = None,
    operation_extensions: Optional[dict[str, Any]] = None,
    validation_rules: Optional[tuple[type[ASTValidationRule], ...]] = None,
) -> AsyncGenerator[ExecutionResult, None]:
    allowed_operation_types = {
        OperationType.SUBSCRIPTION,
    }
    graphql_document = _parse_and_validate(
        schema,
        query,
        allowed_operation_types,
        validation_rules,
        operation_name,
    )
    return _subscribe_generator(
        schema,
        graphql_document,
        root_value,
        variable_values,
        operation_name,
        context_value,
        middleware_manager,
        execution_context_class,
        operation_extensions,
        validation_rules,
    )


async def _subscribe_generator(
    schema: GraphQLSchema,
    graphql_document: DocumentNode,
    root_value: Optional[Any] = None,
    variable_values: Optional[dict[str, Any]] = None,
    operation_name: Optional[str] = None,
    context_value: Optional[Any] = None,
    middleware_manager: Optional[MiddlewareManager] = None,
    execution_context_class: Optional[type[ExecutionContext]] = None,
    operation_extensions: Optional[dict[str, Any]] = None,
    validation_rules: Optional[tuple[type[ASTValidationRule], ...]] = None,
) -> AsyncGenerator[ExecutionResult, None]:
    try:
        # async with extensions_runner.executing():
        assert graphql_document is not None
        gql_33_kwargs = {
            "middleware": middleware_manager,
            "execution_context_class": execution_context_class,
        }
        try:
            # Might not be awaitable for pre-execution errors.
            aiter_or_result: OriginSubscriptionResult = await await_maybe(
                graphql_subscribe(
                    schema,
                    graphql_document,
                    root_value=root_value,
                    variable_values=variable_values,
                    operation_name=operation_name,
                    context_value=context_value,
                    **{} if IS_GQL_32 else gql_33_kwargs,  # type: ignore[arg-type]
                )
            )
        # graphql-core 3.2 doesn't handle some of the pre-execution errors.
        # see `test_subscription_immediate_error`
        except Exception as exc:  # noqa: BLE001
            aiter_or_result = ExecutionResult(data=None, errors=[_coerce_error(exc)])

        # Handle pre-execution errors.
        if isinstance(aiter_or_result, ExecutionResult):
            if aiter_or_result.errors:
                raise GraphQLValidationError(aiter_or_result.errors)
        else:
            try:
                async with aclosing(aiter_or_result):
                    async for result in aiter_or_result:
                        yield _handle_execution_result(
                            result,
                            # extensions_runner,
                        )
            # graphql-core doesn't handle exceptions raised while executing.
            except Exception as exc:  # noqa: BLE001
                yield _handle_execution_result(
                    ExecutionResult(data=None, errors=[_coerce_error(exc)]),
                    # extensions_runner,
                )
    # catch exceptions raised in `on_execute` hook.
    except Exception as exc:  # noqa: BLE001
        origin_result = ExecutionResult(data=None, errors=[_coerce_error(exc)])
        yield _handle_execution_result(
            origin_result,
            # extensions_runner,
        )


def as_str(self) -> str:
    return print_schema(self)


__str__ = as_str


def introspect(schema: GraphQLSchema) -> dict[str, Any]:
    """Return the introspection query result for the current schema.

    Raises:
        ValueError: If the introspection query fails due to an invalid schema
    """
    introspection = execute_sync(schema, get_introspection_query())
    if introspection.errors or not introspection.data:
        raise ValueError(f"Invalid Schema. Errors {introspection.errors!r}")

    return introspection.data


def process_errors(
    errors: list[GraphQLError],
) -> None:
    for error in errors:
        GraphQLServerLogger.error(error)


__all__ = ["Schema", "execute", "execute_sync", "introspect", "subscribe"]
