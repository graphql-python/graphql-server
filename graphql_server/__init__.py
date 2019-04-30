"""
GraphQL-Server-Core
===================

GraphQL-Server-Core is a base library that serves as a helper
for building GraphQL servers or integrations into existing web frameworks using
[GraphQL-Core](https://github.com/graphql-python/graphql-core).
"""


import json
from collections import MutableMapping, namedtuple

import six
from graphql import get_default_backend
from graphql.error import format_error as default_format_error
from graphql.execution import ExecutionResult

from .error import HttpQueryError

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import List, Dict, Optional, Tuple, Any, Union, Callable, Type
    from graphql import GraphQLSchema, GraphQLBackend


__all__ = [
    "run_http_query",
    "encode_execution_results",
    "load_json_body",
    "HttpQueryError"]


# The public helper functions


def run_http_query(
    schema,  # type: GraphQLSchema
    request_method,  # type: str
    data,  # type: Union[Dict, List[Dict]]
    query_data=None,  # type: Optional[Dict]
    batch_enabled=False,  # type: bool
    catch=False,  # type: bool
    **execute_options  # type: Dict
):
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

    This functions returns a tuple with the list of ExecutionResults as first item
    and the list of parameters that have been used for execution as second item.
    """
    if request_method not in ("get", "post"):
        raise HttpQueryError(
            405,
            "GraphQL only supports GET and POST requests.",
            headers={"Allow": "GET, POST"},
        )
    if catch:
        catch_exc = (
            HttpQueryError
        )  # type: Union[Type[HttpQueryError], Type[_NoException]]
    else:
        catch_exc = _NoException
    is_batch = isinstance(data, list)

    is_get_request = request_method == "get"
    allow_only_query = is_get_request

    if not is_batch:
        if not isinstance(data, (dict, MutableMapping)):
            raise HttpQueryError(
                400, "GraphQL params should be a dict. Received {}.".format(data)
            )
        data = [data]
    elif not batch_enabled:
        raise HttpQueryError(400, "Batch GraphQL requests are not enabled.")

    if not data:
        raise HttpQueryError(400, "Received an empty list in the batch request.")

    extra_data = {}  # type: Dict[str, Any]
    # If is a batch request, we don't consume the data from the query
    if not is_batch:
        extra_data = query_data or {}

    all_params = [get_graphql_params(entry, extra_data) for entry in data]

    responses = [
        get_response(schema, params, catch_exc, allow_only_query, **execute_options)
        for params in all_params
    ]

    return responses, all_params


def encode_execution_results(
    execution_results,  # type: List[Optional[ExecutionResult]]
    format_error=None,  # type: Callable[[Exception], Dict]
    is_batch=False,  # type: bool
    encode=None,  # type: Callable[[Dict], Any]
):
    # type: (...) -> Tuple[Any, int]
    """Serialize the ExecutionResults.

    This function takes the ExecutionResults that are returned by run_http_query()
    and serializes them using JSON to produce an HTTP response.
    If you set is_batch=True, then all ExecutionResults will be returned, otherwise only
    the first one will be used. You can also pass a custom function that formats the
    errors in the ExecutionResults, expecting a dictionary as result and another custom
    function that is used to serialize the output.
    """
    responses = [
        format_execution_result(execution_result, format_error or default_format_error)
        for execution_result in execution_results
    ]
    result, status_codes = zip(*responses)
    status_code = max(status_codes)

    if not is_batch:
        result = result[0]

    return (encode or json_encode)(result), status_code


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

GraphQLParams = namedtuple("GraphQLParams", "query variables operation_name")

GraphQLResponse = namedtuple("GraphQLResponse", "result status_code")


class _NoException(Exception):
    """Private exception used when we don't want to catch any real exception."""


def get_graphql_params(data, query_data):
    # type: (Dict, Dict) -> GraphQLParams
    """Fetch GraphQL query, variables and operation name parameters from given data.

    You need to pass both the data from the HTTP request body and the HTTP query string.
    Params from the request body will take precedence over those from the query string.

    You will get a GraphQLParams object with these parameters as attributes in return.
    """
    query = data.get("query") or query_data.get("query")
    variables = data.get("variables") or query_data.get("variables")
    # document_id = data.get('documentId')
    operation_name = data.get("operationName") or query_data.get("operationName")

    return GraphQLParams(query, load_json_variables(variables), operation_name)


def load_json_variables(variables):
    # type: (Optional[Union[str, Dict]]) -> Optional[Dict]
    """Return the given GraphQL variables as a dictionary.

    The function returns the given GraphQL variables, making sure they are
    deserialized from JSON to a dictionary first if necessary. In case of
    invalid JSON input, an HttpQueryError will be raised.
    """
    if variables and isinstance(variables, six.string_types):
        try:
            return json.loads(variables)
        except Exception:
            raise HttpQueryError(400, "Variables are invalid JSON.")
    return variables  # type: ignore


def execute_graphql_request(
    schema,  # type: GraphQLSchema
    params,  # type: GraphQLParams
    allow_only_query=False,  # type: bool
    backend=None,  # type: GraphQLBackend
    **kwargs  # type: Dict
):
    """Execute a GraphQL request and return a ExecutionResult.

    You need to pass the GraphQL schema and the GraphQLParams that you can get
    with the get_graphql_params() function. If you only want to allow GraphQL query
    operations, then set allow_only_query=True. You can also specify a custom
    GraphQLBackend instance that shall be used by GraphQL-Core instead of the
    default one. All other keyword arguments are passed on to the GraphQL-Core
    function for executing GraphQL queries.
    """
    if not params.query:
        raise HttpQueryError(400, "Must provide query string.")

    try:
        if not backend:
            backend = get_default_backend()
        document = backend.document_from_string(schema, params.query)
    except Exception as e:
        return ExecutionResult(errors=[e], invalid=True)

    if allow_only_query:
        operation_type = document.get_operation_type(params.operation_name)
        if operation_type and operation_type != "query":
            raise HttpQueryError(
                405,
                "Can only perform a {} operation from a POST request.".format(
                    operation_type
                ),
                headers={"Allow": "POST"},
            )

    try:
        return document.execute(
            operation_name=params.operation_name, variables=params.variables, **kwargs
        )
    except Exception as e:
        return ExecutionResult(errors=[e], invalid=True)


def get_response(
    schema,  # type: GraphQLSchema
    params,  # type: GraphQLParams
    catch_exc,  # type: Type[BaseException]
    allow_only_query=False,  # type: bool
    **kwargs  # type: Dict
):
    # type: (...) -> Optional[ExecutionResult]
    """Get an individual execution result as response, with option to catch errors.

    This does the same as execute_graphql_request() except that you can catch errors
    that belong to an exception class that you need to pass as a parameter.
    """

    try:
        execution_result = execute_graphql_request(
            schema, params, allow_only_query, **kwargs
        )
    except catch_exc:
        return None

    return execution_result


def format_execution_result(
    execution_result,  # type: Optional[ExecutionResult]
    format_error,  # type: Optional[Callable[[Exception], Dict]]
):
    # type: (...) -> GraphQLResponse
    """Format an execution result into a GraphQLResponse.

    This converts the given execution result into a GraphQLResponse that contains
    the ExecutionResult converted to a dictionary and an appropriate status code.
    """
    status_code = 200

    if execution_result:
        if execution_result.invalid:
            status_code = 400
        response = execution_result.to_dict(format_error=format_error)
    else:
        response = None

    return GraphQLResponse(response, status_code)


def json_encode(data, pretty=False):
    # type: (Union[Dict,List], bool) -> str
    """Serialize the given data using JSON.

    The given data (a dictionary or a list) will be serialized using JSON
    and returned as a string that will be nicely formatted if you set pretty=True.
    """
    if not pretty:
        return json.dumps(data, separators=(",", ":"))

    return json.dumps(data, indent=2, separators=(",", ": "))
