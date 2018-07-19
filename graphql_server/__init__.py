import json
from collections import namedtuple, MutableMapping

import six
from graphql import get_default_backend
from graphql.error import format_error as default_format_error
from graphql.execution import ExecutionResult

from .error import HttpQueryError

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import List, Dict, Optional, Tuple, Any, Union, Callable, Type
    from graphql import GraphQLSchema, GraphQLBackend


class SkipException(Exception):
    pass


GraphQLParams = namedtuple("GraphQLParams", "query,variables,operation_name")
GraphQLResponse = namedtuple("GraphQLResponse", "result,status_code")


def run_http_query(
    schema,  # type: GraphQLSchema
    request_method,  # type: str
    data,  # type: Union[Dict, List[Dict]]
    query_data=None,  # type: Optional[Dict]
    batch_enabled=False,  # type: bool
    catch=False,  # type: bool
    **execute_options  # type: Dict
):
    if request_method not in ("get", "post"):
        raise HttpQueryError(
            405,
            "GraphQL only supports GET and POST requests.",
            headers={"Allow": "GET, POST"},
        )
    if catch:
        catch_exc = (
            HttpQueryError
        )  # type: Union[Type[HttpQueryError], Type[SkipException]]
    else:
        catch_exc = SkipException
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
    format_error,  # type: Callable[[Exception], Dict]
    is_batch,  # type: bool
    encode,  # type: Callable[[Dict], Any]
):
    # type: (...) -> Tuple[Any, int]
    responses = [
        format_execution_result(execution_result, format_error)
        for execution_result in execution_results
    ]
    result, status_codes = zip(*responses)
    status_code = max(status_codes)

    if not is_batch:
        result = result[0]

    return encode(result), status_code


def json_encode(data, pretty=False):
    # type: (Dict, bool) -> str
    if not pretty:
        return json.dumps(data, separators=(",", ":"))

    return json.dumps(data, indent=2, separators=(",", ": "))


def load_json_variables(variables):
    # type: (Optional[Union[str, Dict]]) -> Optional[Dict]
    if variables and isinstance(variables, six.string_types):
        try:
            return json.loads(variables)
        except Exception:
            raise HttpQueryError(400, "Variables are invalid JSON.")
    return variables  # type: ignore


def get_graphql_params(data, query_data):
    # type: (Dict, Dict) -> GraphQLParams
    query = data.get("query") or query_data.get("query")
    variables = data.get("variables") or query_data.get("variables")
    # document_id = data.get('documentId')
    operation_name = data.get("operationName") or query_data.get("operationName")

    return GraphQLParams(query, load_json_variables(variables), operation_name)


def get_response(
    schema,  # type: GraphQLSchema
    params,  # type: GraphQLParams
    catch,  # type: Type[BaseException]
    allow_only_query=False,  # type: bool
    **kwargs  # type: Dict
):
    # type: (...) -> Optional[ExecutionResult]
    try:
        execution_result = execute_graphql_request(
            schema, params, allow_only_query, **kwargs
        )
    except catch:
        return None

    return execution_result


def format_execution_result(
    execution_result,  # type: Optional[ExecutionResult]
    format_error,  # type: Optional[Callable[[Exception], Dict]]
):
    # type: (...) -> GraphQLResponse
    status_code = 200

    if execution_result:
        if execution_result.invalid:
            status_code = 400
        response = execution_result.to_dict(format_error=format_error)
    else:
        response = None

    return GraphQLResponse(response, status_code)


def execute_graphql_request(
    schema,  # type: GraphQLSchema
    params,  # type: GraphQLParams
    allow_only_query=False,  # type: bool
    backend=None,  # type: GraphQLBackend
    **kwargs  # type: Dict
):
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


def load_json_body(data):
    # type: (str) -> Dict
    try:
        return json.loads(data)
    except Exception:
        raise HttpQueryError(400, "POST body sent invalid JSON.")


__all__ = [
    "HttpQueryError",
    "default_format_error",
    "SkipException",
    "run_http_query",
    "encode_execution_results",
    "json_encode",
    "load_json_variables",
    "get_graphql_params",
    "get_response",
    "format_execution_result",
    "execute_graphql_request",
    "load_json_body",
]
