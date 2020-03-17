"""
GraphQL-Server-Core
===================

GraphQL-Server-Core is a base library that serves as a helper
for building GraphQL servers or integrations into existing web frameworks using
[GraphQL-Core](https://github.com/graphql-python/graphql-core).
"""


import json
from collections import namedtuple, MutableMapping
from typing import Optional, List, Callable, Dict, Any, Union, Type

from graphql import (GraphQLSchema, ExecutionResult, GraphQLError, parse, get_operation_ast,
                     validate_schema, validate, execute)
from graphql import format_error as format_error_default

from promise import promisify, Promise

from .error import HttpQueryError


__all__ = [
    "run_http_query",
    "encode_execution_results",
    "load_json_body",
    "json_encode",
    "HttpQueryError",
    "GraphQLParams",
    "GraphQLResponse",
    "ServerResponse",
]


# The public data structures

GraphQLParams = namedtuple("GraphQLParams", "query variables operation_name")
GraphQLResponse = namedtuple("GraphQLResponse", "results params")
ServerResponse = namedtuple("ServerResponse", "body status_code")


# The public helper functions


def run_http_query(
    schema: GraphQLSchema,
    request_method: str,
    data: Union[Dict, List[Dict]],
    query_data: Optional[Dict] = None,
    batch_enabled: bool = False,
    catch: bool = False,
    **execute_options: Dict[str, Any]
) -> GraphQLResponse:
    """Execute GraphQL coming from an HTTP query against a given schema.

    You need to pass the schema (that is supposed to be already validated),
    the request_method (that must be either "get" or "post"),
    the data from the HTTP request body, and the data from the query string.
    By default, only one parameter set is expected, but if you set batch_enabled,
    you can pass data that contains a list of parameter sets to run multiple
    queries as a batch execution using a single HTTP request. You can specify
    whether results returning HTTPQueryErrors should be caught and skipped.
    All other keyword arguments are passed on to the GraphQL-Core function for
    executing GraphQL queries.

    Returns a ServerResults tuple with the list of ExecutionResults as first item
    and the list of parameters that have been used for execution as second item.
    """
    if not isinstance(schema, GraphQLSchema):
        raise TypeError(f"Expected a GraphQL schema, but received {schema!r}.")
    if request_method not in ("get", "post"):
        raise HttpQueryError(
            405,
            "GraphQL only supports GET and POST requests.",
            headers={"Allow": "GET, POST"},
        )
    if catch:
        catch_exc: Union[Type[HttpQueryError], Type[_NoException]] = HttpQueryError
    else:
        catch_exc = _NoException
    is_batch = isinstance(data, list)

    is_get_request = request_method == "get"
    allow_only_query = is_get_request

    if not is_batch:
        if not isinstance(data, (dict, MutableMapping)):
            raise HttpQueryError(
                400, f"GraphQL params should be a dict. Received {data!r}."
            )
        data = [data]
    elif not batch_enabled:
        raise HttpQueryError(400, "Batch GraphQL requests are not enabled.")

    if not data:
        raise HttpQueryError(400, "Received an empty list in the batch request.")

    extra_data: Dict[str, Any] = {}
    # If is a batch request, we don't consume the data from the query
    if not is_batch:
        extra_data = query_data or {}

    all_params: List[GraphQLParams] = [get_graphql_params(entry, extra_data) for entry in data]

    results = [get_response(schema, params, catch_exc, allow_only_query, **execute_options) for params in all_params]

    return GraphQLResponse(results, all_params)


def json_encode(data: Union[Dict, List], pretty: bool = False) -> str:
    """Serialize the given data(a dictionary or a list) using JSON.

    The given data (a dictionary or a list) will be serialized using JSON
    and returned as a string that will be nicely formatted if you set pretty=True.
    """
    if not pretty:
        return json.dumps(data, separators=(",", ":"))
    return json.dumps(data, indent=2, separators=(",", ": "))


def encode_execution_results(
    execution_results: List[Optional[ExecutionResult]],
    format_error: Callable[[Exception], Dict],
    is_batch: bool = False,
    encode: Callable[[Dict], Any] = json_encode,
) -> ServerResponse:
    """Serialize the ExecutionResults.

    This function takes the ExecutionResults that are returned by run_http_query()
    and serializes them using JSON to produce an HTTP response.
    If you set is_batch=True, then all ExecutionResults will be returned, otherwise only
    the first one will be used. You can also pass a custom function that formats the
    errors in the ExecutionResults, expecting a dictionary as result and another custom
    function that is used to serialize the output.

    Returns a ServerResponse tuple with the serialized response as the first item and
    a status code of 200 or 400 in case any result was invalid as the second item.
    """
    results = [
        format_execution_result(execution_result, format_error)
        for execution_result in execution_results
    ]
    result, status_codes = zip(*results)
    status_code = max(status_codes)

    if not is_batch:
        result = result[0]

    return ServerResponse(encode(result), status_code)


def load_json_body(data):
    # type: (str) -> Union[Dict, List]
    """Load the request body as a dictionary or a list.

    The body must be passed in a string and will be deserialized from JSON,
    raising an HttpQueryError in case of invalid JSON.
    """
    try:
        return json.loads(data)
    except Exception:
        raise HttpQueryError(400, "POST body sent invalid JSON.")


# Some more private helpers

FormattedResult = namedtuple("FormattedResult", "result status_code")


class _NoException(Exception):
    """Private exception used when we don't want to catch any real exception."""


def get_graphql_params(data: Dict, query_data: Dict) -> GraphQLParams:
    """Fetch GraphQL query, variables and operation name parameters from given data.

    You need to pass both the data from the HTTP request body and the HTTP query string.
    Params from the request body will take precedence over those from the query string.

    You will get a RequestParams tuple with these parameters in return.
    """
    query = data.get("query") or query_data.get("query")
    variables = data.get("variables") or query_data.get("variables")
    # document_id = data.get('documentId')
    operation_name = data.get("operationName") or query_data.get("operationName")

    return GraphQLParams(query, load_json_variables(variables), operation_name)


def load_json_variables(variables: Optional[Union[str, Dict]]) -> Optional[Dict]:
    """Return the given GraphQL variables as a dictionary.

    The function returns the given GraphQL variables, making sure they are
    deserialized from JSON to a dictionary first if necessary. In case of
    invalid JSON input, an HttpQueryError will be raised.
    """
    if variables and isinstance(variables, str):
        try:
            return json.loads(variables)
        except Exception:
            raise HttpQueryError(400, "Variables are invalid JSON.")
    return variables  # type: ignore


def execute_graphql_request(
    schema: GraphQLSchema,
    params: GraphQLParams,
    allow_only_query: bool = False,
    **kwargs
) -> ExecutionResult:
    """Execute a GraphQL request and return an ExecutionResult.

    You need to pass the GraphQL schema and the GraphQLParams that you can get
    with the get_graphql_params() function. If you only want to allow GraphQL query
    operations, then set allow_only_query=True. You can also specify a custom
    GraphQLBackend instance that shall be used by GraphQL-Core instead of the
    default one. All other keyword arguments are passed on to the GraphQL-Core
    function for executing GraphQL queries.
    """
    if not params.query:
        raise HttpQueryError(400, "Must provide query string.")

    # Validate the schema and return a list of errors if it does not satisfy the Type System.
    schema_validation_errors = validate_schema(schema)
    if schema_validation_errors:
        return ExecutionResult(data=None, errors=schema_validation_errors)

    # Parse the query and return ExecutionResult with errors found.
    # Any Exception is parsed as GraphQLError.
    try:
        document = parse(params.query)
    except GraphQLError as e:
        return ExecutionResult(data=None, errors=[e])
    except Exception as e:
        e = GraphQLError(str(e), original_error=e)
        return ExecutionResult(data=None, errors=[e])

    if allow_only_query:
        operation_ast = get_operation_ast(document, params.operation_name)
        if operation_ast:
            operation = operation_ast.operation.value
            if operation != 'query':
                raise HttpQueryError(
                    405,
                    f"Can only perform a {operation} operation from a POST request.",
                    headers={"Allow": "POST"},
                )

    validation_errors = validate(schema, document)
    if validation_errors:
        return ExecutionResult(data=None, errors=validation_errors)

    return execute(schema, document, variable_values=params.variables, operation_name=params.operation_name, **kwargs)


@promisify
def execute_graphql_request_as_promise(*args, **kwargs):
    return execute_graphql_request(*args, **kwargs)


def get_response(
    schema: GraphQLSchema,
    params: GraphQLParams,
    catch_exc: Type[BaseException],
    allow_only_query: bool = False,
    **kwargs
) -> Optional[Union[ExecutionResult, Promise[ExecutionResult]]]:
    """Get an individual execution result as response, with option to catch errors.

    This does the same as execute_graphql_request() except that you can catch errors
    that belong to an exception class that you need to pass as a parameter.
    """
    # Note: PyCharm will display a error due to the triple dot being used on Callable.
    execute_request: Callable[..., Union[Promise[ExecutionResult], ExecutionResult]] = execute_graphql_request
    if kwargs.get("return_promise", False):
        execute_request = execute_graphql_request_as_promise

    # noinspection PyBroadException
    try:
        execution_result = execute_request(schema, params, allow_only_query, **kwargs)
    except catch_exc:
        return None

    return execution_result


def format_execution_result(
    execution_result: Optional[ExecutionResult],
    format_error: Optional[Callable[[Exception], Dict]] = format_error_default
) -> GraphQLResponse:
    """Format an execution result into a GraphQLResponse.

    This converts the given execution result into a FormattedResult that contains
    the ExecutionResult converted to a dictionary and an appropriate status code.
    """
    status_code = 200
    response: Optional[Dict[str, Any]] = None

    if execution_result:
        if execution_result.errors:
            response = {"errors": [format_error(e) for e in execution_result.errors]}
            status_code = 400
        else:
            response = {'data': execution_result.data}

    return FormattedResult(response, status_code)
