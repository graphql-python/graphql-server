from pytest import raises
import json

from graphql.execution import ExecutionResult
from graphql_server import run_http_query, GraphQLParams, HttpQueryError, default_format_error
from .schema import schema


def execution_to_dict(execution_result):
    result = {}
    if execution_result.invalid:
        result["errors"] = [default_format_error(e) for e in execution_result.errors]
    if execution_result.data:
        result["data"] = execution_result.data

    return result


def executions_to_dict(execution_results):
    return map(execution_to_dict, execution_results)


def test_allows_get_with_query_param():
    query = '{test}'
    results, params = run_http_query(schema, 'get', {}, query_data=dict(query=query))

    assert executions_to_dict(results) == [{
        'data': {'test': "Hello World"},
    }]
    assert params == [GraphQLParams(query=query,variables=None,operation_name=None)]


def test_allows_get_with_variable_values():
    query = '{test}'
    results, params = run_http_query(schema, 'get', {}, query_data=dict(
        query='query helloWho($who: String){ test(who: $who) }',
        variables=json.dumps({'who': "Dolly"})
    ))

    assert executions_to_dict(results) == [{
        'data': {'test': "Hello Dolly"},
    }]


def test_allows_get_with_operation_name():
    results, params = run_http_query(schema, 'get', {}, query_data=dict(
        query='''
        query helloYou { test(who: "You"), ...shared }
        query helloWorld { test(who: "World"), ...shared }
        query helloDolly { test(who: "Dolly"), ...shared }
        fragment shared on QueryRoot {
          shared: test(who: "Everyone")
        }
        ''',
        operationName='helloWorld'
    ))

    assert executions_to_dict(results) == [{
        'data': {
            'test': 'Hello World',
            'shared': 'Hello Everyone'
        },
    }]


def test_reports_validation_errors():
    results, params = run_http_query(schema, 'get', {}, query_data=dict(
        query='{ test, unknownOne, unknownTwo }'
    ))

    assert executions_to_dict(results) == [{
        'errors': [
            {
                'message': 'Cannot query field "unknownOne" on type "QueryRoot".',
                'locations': [{'line': 1, 'column': 9}]
            },
            {
                'message': 'Cannot query field "unknownTwo" on type "QueryRoot".',
                'locations': [{'line': 1, 'column': 21}]
            }
        ]
    }]


def test_errors_when_missing_operation_name():
    results, params = run_http_query(schema, 'get', {}, query_data=dict(
        query='''
        query TestQuery { test }
        mutation TestMutation { writeTest { test } }
        '''
    ))

    assert executions_to_dict(results) == [{
        'errors': [
            {
                'message': 'Must provide operation name if query contains multiple operations.'
            }
        ]
    }]


# def test_errors_when_sending_a_mutation_via_get():
#     results, params = run_http_query(schema, 'get', {}, query_data=dict(
#         query='''
#         mutation TestMutation { writeTest { test } }
#         '''
#     ))

#     assert executions_to_dict(results) == [{
#         'errors': [
#             {
#                 'message': 'Can only perform a mutation operation from a POST request.'
#             }
#         ]
#     }]


# def test_errors_when_selecting_a_mutation_within_a_get(client):
#     response = client.get(url_string(
#         query='''
#         query TestQuery { test }
#         mutation TestMutation { writeTest { test } }
#         ''',
#         operationName='TestMutation'
#     ))

#     assert response.status_code == 405
#     assert response_json(response) == {
#         'errors': [
#             {
#                 'message': 'Can only perform a mutation operation from a POST request.'
#             }
#         ]
#     }


# def test_allows_mutation_to_exist_within_a_get(client):
#     response = client.get(url_string(
#         query='''
#         query TestQuery { test }
#         mutation TestMutation { writeTest { test } }
#         ''',
#         operationName='TestQuery'
#     ))

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello World"}
#     }


# def test_allows_post_with_json_encoding(client):
#     response = client.post(url_string(), data=j(query='{test}'), content_type='application/json')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello World"}
#     }


# def test_allows_sending_a_mutation_via_post(client):
#     response = client.post(url_string(), data=j(query='mutation TestMutation { writeTest { test } }'), content_type='application/json')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'writeTest': {'test': 'Hello World'}}
#     }


# def test_allows_post_with_url_encoding(client):
#     response = client.post(url_string(), data=urlencode(dict(query='{test}')), content_type='application/x-www-form-urlencoded')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello World"}
#     }


# def test_supports_post_json_query_with_string_variables(client):
#     response = client.post(url_string(), data=j(
#         query='query helloWho($who: String){ test(who: $who) }',
#         variables=json.dumps({'who': "Dolly"})
#     ), content_type='application/json')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello Dolly"}
#     }


# def test_supports_post_json_query_with_json_variables(client):
#     response = client.post(url_string(), data=j(
#         query='query helloWho($who: String){ test(who: $who) }',
#         variables={'who': "Dolly"}
#     ), content_type='application/json')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello Dolly"}
#     }


# def test_supports_post_url_encoded_query_with_string_variables(client):
#     response = client.post(url_string(), data=urlencode(dict(
#         query='query helloWho($who: String){ test(who: $who) }',
#         variables=json.dumps({'who': "Dolly"})
#     )), content_type='application/x-www-form-urlencoded')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello Dolly"}
#     }


# def test_supports_post_json_quey_with_get_variable_values(client):
#     response = client.post(url_string(
#         variables=json.dumps({'who': "Dolly"})
#     ), data=j(
#         query='query helloWho($who: String){ test(who: $who) }',
#     ), content_type='application/json')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello Dolly"}
#     }


# def test_post_url_encoded_query_with_get_variable_values(client):
#     response = client.post(url_string(
#         variables=json.dumps({'who': "Dolly"})
#     ), data=urlencode(dict(
#         query='query helloWho($who: String){ test(who: $who) }',
#     )), content_type='application/x-www-form-urlencoded')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello Dolly"}
#     }


# def test_supports_post_raw_text_query_with_get_variable_values(client):
#     response = client.post(url_string(
#         variables=json.dumps({'who': "Dolly"})
#     ),
#         data='query helloWho($who: String){ test(who: $who) }',
#         content_type='application/graphql'
#     )

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {'test': "Hello Dolly"}
#     }


# def test_allows_post_with_operation_name(client):
#     response = client.post(url_string(), data=j(
#         query='''
#         query helloYou { test(who: "You"), ...shared }
#         query helloWorld { test(who: "World"), ...shared }
#         query helloDolly { test(who: "Dolly"), ...shared }
#         fragment shared on QueryRoot {
#           shared: test(who: "Everyone")
#         }
#         ''',
#         operationName='helloWorld'
#     ), content_type='application/json')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {
#             'test': 'Hello World',
#             'shared': 'Hello Everyone'
#         }
#     }


# def test_allows_post_with_get_operation_name(client):
#     response = client.post(url_string(
#         operationName='helloWorld'
#     ), data='''
#     query helloYou { test(who: "You"), ...shared }
#     query helloWorld { test(who: "World"), ...shared }
#     query helloDolly { test(who: "Dolly"), ...shared }
#     fragment shared on QueryRoot {
#       shared: test(who: "Everyone")
#     }
#     ''',
#         content_type='application/graphql')

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {
#             'test': 'Hello World',
#             'shared': 'Hello Everyone'
#         }
#     }


# @pytest.mark.parametrize('app', [create_app(pretty=True)])
# def test_supports_pretty_printing(client):
#     response = client.get(url_string(query='{test}'))

#     assert response.data.decode() == (
#         '{\n'
#         '  "data": {\n'
#         '    "test": "Hello World"\n'
#         '  }\n'
#         '}'
#     )


# @pytest.mark.parametrize('app', [create_app(pretty=False)])
# def test_not_pretty_by_default(client):
#     response = client.get(url_string(query='{test}'))

#     assert response.data.decode() == (
#         '{"data":{"test":"Hello World"}}'
#     )


# def test_supports_pretty_printing_by_request(client):
#     response = client.get(url_string(query='{test}', pretty='1'))

#     assert response.data.decode() == (
#         '{\n'
#         '  "data": {\n'
#         '    "test": "Hello World"\n'
#         '  }\n'
#         '}'
#     )


# def test_handles_field_errors_caught_by_graphql(client):
#     response = client.get(url_string(query='{thrower}'))
#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': None,
#         'errors': [{'locations': [{'column': 2, 'line': 1}], 'message': 'Throws!'}]
#     }


# def test_handles_syntax_errors_caught_by_graphql(client):
#     response = client.get(url_string(query='syntaxerror'))
#     assert response.status_code == 400
#     assert response_json(response) == {
#         'errors': [{'locations': [{'column': 1, 'line': 1}],
#                     'message': 'Syntax Error GraphQL request (1:1) '
#                                'Unexpected Name "syntaxerror"\n\n1: syntaxerror\n   ^\n'}]
#     }


# def test_handles_errors_caused_by_a_lack_of_query(client):
#     response = client.get(url_string())

#     assert response.status_code == 400
#     assert response_json(response) == {
#         'errors': [{'message': 'Must provide query string.'}]
#     }


# def test_handles_batch_correctly_if_is_disabled(client):
#     response = client.post(url_string(), data='[]', content_type='application/json')

#     assert response.status_code == 400
#     assert response_json(response) == {
#         'errors': [{'message': 'Batch GraphQL requests are not enabled.'}]
#     }


# def test_handles_incomplete_json_bodies(client):
#     response = client.post(url_string(), data='{"query":', content_type='application/json')

#     assert response.status_code == 400
#     assert response_json(response) == {
#         'errors': [{'message': 'POST body sent invalid JSON.'}]
#     }


# def test_handles_plain_post_text(client):
#     response = client.post(url_string(
#         variables=json.dumps({'who': "Dolly"})
#     ),
#         data='query helloWho($who: String){ test(who: $who) }',
#         content_type='text/plain'
#     )
#     assert response.status_code == 400
#     assert response_json(response) == {
#         'errors': [{'message': 'Must provide query string.'}]
#     }


# def test_handles_poorly_formed_variables(client):
#     response = client.get(url_string(
#         query='query helloWho($who: String){ test(who: $who) }',
#         variables='who:You'
#     ))
#     assert response.status_code == 400
#     assert response_json(response) == {
#         'errors': [{'message': 'Variables are invalid JSON.'}]
#     }


def test_handles_unsupported_http_methods():
    with raises(HttpQueryError) as exc_info:
        run_http_query(schema, 'put', None)

    assert exc_info.value == HttpQueryError(
        405,
        'GraphQL only supports GET and POST requests.',
        headers={
            'Allow': 'GET, POST'
        }
    )

# def test_passes_request_into_request_context(client):
#     response = client.get(url_string(query='{request}', q='testing'))

#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {
#             'request': 'testing'
#         }
#     }


# @pytest.mark.parametrize('app', [create_app(get_context=lambda:"CUSTOM CONTEXT")])
# def test_supports_pretty_printing(client):
#     response = client.get(url_string(query='{context}'))


#     assert response.status_code == 200
#     assert response_json(response) == {
#         'data': {
#             'context': 'CUSTOM CONTEXT'
#         }
#     }


# def test_post_multipart_data(client):
#     query = 'mutation TestMutation { writeTest { test } }'
#     response = client.post(
#         url_string(),
#         data= {
#             'query': query,
#             'file': (StringIO(), 'text1.txt'),
#         },
#         content_type='multipart/form-data'
#     )

#     assert response.status_code == 200
#     assert response_json(response) == {'data': {u'writeTest': {u'test': u'Hello World'}}}


# @pytest.mark.parametrize('app', [create_app(batch=True)])
# def test_batch_allows_post_with_json_encoding(client):
#     response = client.post(
#         url_string(),
#         data=jl(
#             # id=1,
#             query='{test}'
#         ),
#         content_type='application/json'
#     )

#     assert response.status_code == 200
#     assert response_json(response) == [{
#         # 'id': 1,
#         'data': {'test': "Hello World"}
#     }]


# @pytest.mark.parametrize('app', [create_app(batch=True)])
# def test_batch_supports_post_json_query_with_json_variables(client):
#     response = client.post(
#         url_string(),
#         data=jl(
#             # id=1,
#             query='query helloWho($who: String){ test(who: $who) }',
#             variables={'who': "Dolly"}
#         ),
#         content_type='application/json'
#     )

#     assert response.status_code == 200
#     assert response_json(response) == [{
#         # 'id': 1,
#         'data': {'test': "Hello Dolly"}
#     }]
 
          
# @pytest.mark.parametrize('app', [create_app(batch=True)])
# def test_batch_allows_post_with_operation_name(client):
#     response = client.post(
#         url_string(),
#         data=jl(
#             # id=1,
#             query='''
#             query helloYou { test(who: "You"), ...shared }
#             query helloWorld { test(who: "World"), ...shared }
#             query helloDolly { test(who: "Dolly"), ...shared }
#             fragment shared on QueryRoot {
#               shared: test(who: "Everyone")
#             }
#             ''',
#             operationName='helloWorld'
#         ),
#         content_type='application/json'
#     )

#     assert response.status_code == 200
#     assert response_json(response) == [{
#         # 'id': 1,
#         'data': {
#             'test': 'Hello World',
#             'shared': 'Hello Everyone'
#         }
#     }]
