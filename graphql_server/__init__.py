import json
from collections import MutableMapping, namedtuple

import six

from graphql import Source, execute, parse, validate
from graphql.error import format_error as format_graphql_error
from graphql.error import GraphQLError
from graphql.execution import ExecutionResult
from graphql.utils.get_operation_ast import get_operation_ast
from promise import promisify

from .error import HttpQueryError


class SkipException(Exception):
    pass


GraphQLParams = namedtuple('GraphQLParams', 'query,variables,operation_name')
GraphQLResponse = namedtuple('GraphQLResponse', 'result,status_code')


def default_format_error(error):
    if isinstance(error, GraphQLError):
        return format_graphql_error(error)

    return {'message': six.text_type(error)}


def run_http_query(schema, request_method, data, query_data=None, batch_enabled=False, catch=False, **execute_options):
    if request_method not in ('get', 'post'):
        raise HttpQueryError(
            405,
            'GraphQL only supports GET and POST requests.',
            headers={
                'Allow': 'GET, POST'
            }
        )
    if catch:
        catch = HttpQueryError
    else:
        catch = SkipException
    is_batch = isinstance(data, list)

    is_get_request = request_method == 'get'
    allow_only_query = is_get_request

    if not is_batch:
        if not isinstance(data, (dict, MutableMapping)):
            raise HttpQueryError(
                400,
                'GraphQL params should be a dict. Received {}.'.format(data)
            )
        data = [data]
    elif not batch_enabled:
        raise HttpQueryError(
            400,
            'Batch GraphQL requests are not enabled.'
        )

    if not data:
        raise HttpQueryError(
            400,
            'Received an empty list in the batch request.'
        )

    extra_data = {}
    # If is a batch request, we don't consume the data from the query
    if not is_batch:
        extra_data = query_data or {}

    all_params = [get_graphql_params(entry, extra_data) for entry in data]

    responses = [get_response(
        schema,
        params,
        catch,
        allow_only_query,
        **execute_options
    ) for params in all_params]

    return responses, all_params


def encode_execution_results(execution_results, format_error, is_batch, encode):
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
    if not pretty:
        return json.dumps(data, separators=(',', ':'))

    return json.dumps(
        data,
        indent=2,
        separators=(',', ': ')
    )


def load_json_variables(variables):
    if variables and isinstance(variables, six.string_types):
        try:
            return json.loads(variables)
        except:
            raise HttpQueryError(400, 'Variables are invalid JSON.')
    return variables


def get_graphql_params(data, query_data):
    query = data.get('query') or query_data.get('query')
    variables = data.get('variables') or query_data.get('variables')
    # id = data.get('id')
    operation_name = data.get('operationName') or query_data.get('operationName')

    return GraphQLParams(query, load_json_variables(variables), operation_name)


def get_response(schema, params, catch=None, allow_only_query=False, **kwargs):
    try:
        execution_result = execute_graphql(
            schema,
            params,
            allow_only_query,
            **kwargs
        )
    except catch:
        return None

    return execution_result


def format_execution_result(execution_result, format_error):
    status_code = 200

    if execution_result:
        response = {}

        if execution_result.errors:
            response['errors'] = [format_error(e) for e in execution_result.errors]

        if execution_result.invalid:
            status_code = 400
        else:
            status_code = 200
            response['data'] = execution_result.data

    else:
        response = None

    return GraphQLResponse(response, status_code)


def execute_graphql(*args, **kwargs):
    return_promise = kwargs.get('return_promise', False)
    if return_promise:
        return execute_graphql_request_as_promise(*args, **kwargs)
    else:
        return execute_graphql_request(*args, **kwargs)


@promisify
def execute_graphql_request_as_promise(*args, **kwargs):
    return execute_graphql_request(*args, **kwargs)


def execute_graphql_request(schema, params, allow_only_query=False, **kwargs):
    if not params.query:
        raise HttpQueryError(400, 'Must provide query string.')

    try:
        source = Source(params.query, name='GraphQL request')
        ast = parse(source)
        validation_errors = validate(schema, ast)
        if validation_errors:
            return ExecutionResult(
                errors=validation_errors,
                invalid=True,
            )
    except Exception as e:
        return ExecutionResult(errors=[e], invalid=True)

    if allow_only_query:
        operation_ast = get_operation_ast(ast, params.operation_name)
        if operation_ast and operation_ast.operation != 'query':
            raise HttpQueryError(
                405,
                'Can only perform a {} operation from a POST request.'.format(operation_ast.operation),
                headers={
                    'Allow': ['POST'],
                }
            )

    try:
        return execute(
            schema,
            ast,
            operation_name=params.operation_name,
            variable_values=params.variables,
            **kwargs
        )

    except Exception as e:
        return ExecutionResult(errors=[e], invalid=True)


def load_json_body(data):
    try:
        return json.loads(data)
    except:
        raise HttpQueryError(
            400,
            'POST body sent invalid JSON.'
        )
