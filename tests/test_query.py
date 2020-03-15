import json

from graphql.error import GraphQLError, GraphQLSyntaxError
from graphql.execution import ExecutionResult
from promise import Promise
from pytest import raises

from graphql_server import (
    HttpQueryError,
    RequestParams,
    ServerResults,
    encode_execution_results,
    json_encode,
    json_encode_pretty,
    load_json_body,
    run_http_query,
)

from .schema import schema
from .utils import as_dicts


def test_request_params():
    assert issubclass(RequestParams, tuple)
    # noinspection PyUnresolvedReferences
    assert RequestParams._fields == ("query", "variables", "operation_name")


def test_server_results():
    assert issubclass(ServerResults, tuple)
    # noinspection PyUnresolvedReferences
    assert ServerResults._fields == ("results", "params")


def test_allows_get_with_query_param():
    query = "{test}"
    results, params = run_http_query(schema, "get", {}, dict(query=query))

    assert as_dicts(results) == [{"data": {"test": "Hello World"}}]
    assert params == [RequestParams(query=query, variables=None, operation_name=None)]


def test_allows_get_with_variable_values():
    results, params = run_http_query(
        schema,
        "get",
        {},
        dict(
            query="query helloWho($who: String){ test(who: $who) }",
            variables=json.dumps({"who": "Dolly"}),
        ),
    )

    assert as_dicts(results) == [{"data": {"test": "Hello Dolly"}}]


def test_allows_get_with_operation_name():
    results, params = run_http_query(
        schema,
        "get",
        {},
        query_data=dict(
            query="""
        query helloYou { test(who: "You"), ...shared }
        query helloWorld { test(who: "World"), ...shared }
        query helloDolly { test(who: "Dolly"), ...shared }
        fragment shared on QueryRoot {
          shared: test(who: "Everyone")
        }
        """,
            operationName="helloWorld",
        ),
    )

    assert as_dicts(results) == [
        {"data": {"test": "Hello World", "shared": "Hello Everyone"}}
    ]


def test_reports_validation_errors():
    results, params = run_http_query(
        schema, "get", {}, query_data=dict(query="{ test, unknownOne, unknownTwo }")
    )

    assert as_dicts(results) == [
        {
            "errors": [
                {
                    "message": 'Cannot query field "unknownOne" on type "QueryRoot".',
                    "locations": [{"line": 1, "column": 9}],
                },
                {
                    "message": 'Cannot query field "unknownTwo" on type "QueryRoot".',
                    "locations": [{"line": 1, "column": 21}],
                },
            ]
        }
    ]


def test_non_dict_params_in_non_batch_query():
    with raises(HttpQueryError) as exc_info:
        # noinspection PyTypeChecker
        run_http_query(schema, "get", "not a dict")  # type: ignore

    assert exc_info.value == HttpQueryError(
        400, "GraphQL params should be a dict. Received 'not a dict'."
    )


def test_empty_batch_in_batch_query():
    with raises(HttpQueryError) as exc_info:
        run_http_query(schema, "get", [], batch_enabled=True)

    assert exc_info.value == HttpQueryError(
        400, "Received an empty list in the batch request."
    )


def test_errors_when_missing_operation_name():
    results, params = run_http_query(
        schema,
        "get",
        {},
        query_data=dict(
            query="""
        query TestQuery { test }
        mutation TestMutation { writeTest { test } }
        """
        ),
    )

    assert as_dicts(results) == [
        {
            "errors": [
                {
                    "message": (
                        "Must provide operation name"
                        " if query contains multiple operations."
                    )
                }
            ]
        }
    ]
    assert isinstance(results[0].errors[0], GraphQLError)


def test_errors_when_sending_a_mutation_via_get():
    with raises(HttpQueryError) as exc_info:
        run_http_query(
            schema,
            "get",
            {},
            query_data=dict(
                query="""
                mutation TestMutation { writeTest { test } }
                """
            ),
        )

    assert exc_info.value == HttpQueryError(
        405,
        "Can only perform a mutation operation from a POST request.",
        headers={"Allow": "POST"},
    )


def test_catching_errors_when_sending_a_mutation_via_get():
    results, params = run_http_query(
        schema,
        "get",
        {},
        query_data=dict(
            query="""
                mutation TestMutation { writeTest { test } }
                """
        ),
        catch=True,
    )

    assert results == [None]


def test_errors_when_selecting_a_mutation_within_a_get():
    with raises(HttpQueryError) as exc_info:
        run_http_query(
            schema,
            "get",
            {},
            query_data=dict(
                query="""
                query TestQuery { test }
                mutation TestMutation { writeTest { test } }
                """,
                operationName="TestMutation",
            ),
        )

    assert exc_info.value == HttpQueryError(
        405,
        "Can only perform a mutation operation from a POST request.",
        headers={"Allow": "POST"},
    )


def test_allows_mutation_to_exist_within_a_get():
    results, params = run_http_query(
        schema,
        "get",
        {},
        query_data=dict(
            query="""
            query TestQuery { test }
            mutation TestMutation { writeTest { test } }
            """,
            operationName="TestQuery",
        ),
    )

    assert as_dicts(results) == [{"data": {"test": "Hello World"}}]


def test_allows_sending_a_mutation_via_post():
    results, params = run_http_query(
        schema,
        "post",
        {},
        query_data=dict(query="mutation TestMutation { writeTest { test } }"),
    )

    assert as_dicts(results) == [{"data": {"writeTest": {"test": "Hello World"}}}]


def test_allows_post_with_url_encoding():
    results, params = run_http_query(
        schema, "post", {}, query_data=dict(query="{test}")
    )

    assert as_dicts(results) == [{"data": {"test": "Hello World"}}]


def test_supports_post_json_query_with_string_variables():
    results, params = run_http_query(
        schema,
        "post",
        {},
        query_data=dict(
            query="query helloWho($who: String){ test(who: $who) }",
            variables='{"who": "Dolly"}',
        ),
    )

    assert as_dicts(results) == [{"data": {"test": "Hello Dolly"}}]


def test_supports_post_url_encoded_query_with_string_variables():
    results, params = run_http_query(
        schema,
        "post",
        {},
        query_data=dict(
            query="query helloWho($who: String){ test(who: $who) }",
            variables='{"who": "Dolly"}',
        ),
    )

    assert as_dicts(results) == [{"data": {"test": "Hello Dolly"}}]


def test_supports_post_json_query_with_get_variable_values():
    results, params = run_http_query(
        schema,
        "post",
        data=dict(query="query helloWho($who: String){ test(who: $who) }"),
        query_data=dict(variables={"who": "Dolly"}),
    )

    assert as_dicts(results) == [{"data": {"test": "Hello Dolly"}}]


def test_post_url_encoded_query_with_get_variable_values():
    results, params = run_http_query(
        schema,
        "get",
        data=dict(query="query helloWho($who: String){ test(who: $who) }"),
        query_data=dict(variables='{"who": "Dolly"}'),
    )

    assert as_dicts(results) == [{"data": {"test": "Hello Dolly"}}]


def test_supports_post_raw_text_query_with_get_variable_values():
    results, params = run_http_query(
        schema,
        "get",
        data=dict(query="query helloWho($who: String){ test(who: $who) }"),
        query_data=dict(variables='{"who": "Dolly"}'),
    )

    assert as_dicts(results) == [{"data": {"test": "Hello Dolly"}}]


def test_allows_post_with_operation_name():
    results, params = run_http_query(
        schema,
        "get",
        data=dict(
            query="""
            query helloYou { test(who: "You"), ...shared }
            query helloWorld { test(who: "World"), ...shared }
            query helloDolly { test(who: "Dolly"), ...shared }
            fragment shared on QueryRoot {
              shared: test(who: "Everyone")
            }
            """,
            operationName="helloWorld",
        ),
    )

    assert as_dicts(results) == [
        {"data": {"test": "Hello World", "shared": "Hello Everyone"}}
    ]


def test_allows_post_with_get_operation_name():
    results, params = run_http_query(
        schema,
        "get",
        data=dict(
            query="""
            query helloYou { test(who: "You"), ...shared }
            query helloWorld { test(who: "World"), ...shared }
            query helloDolly { test(who: "Dolly"), ...shared }
            fragment shared on QueryRoot {
              shared: test(who: "Everyone")
            }
            """
        ),
        query_data=dict(operationName="helloWorld"),
    )

    assert as_dicts(results) == [
        {"data": {"test": "Hello World", "shared": "Hello Everyone"}}
    ]


def test_supports_pretty_printing_data():
    results, params = run_http_query(schema, "get", dict(query="{test}"))
    body = encode_execution_results(results, encode=json_encode_pretty).body

    assert body == "{\n" '  "data": {\n' '    "test": "Hello World"\n' "  }\n" "}"


def test_not_pretty_data_by_default():
    results, params = run_http_query(schema, "get", dict(query="{test}"))
    body = encode_execution_results(results).body

    assert body == '{"data":{"test":"Hello World"}}'


def test_handles_field_errors_caught_by_graphql():
    results, params = run_http_query(schema, "get", dict(query="{error}"))

    assert as_dicts(results) == [
        {
            "data": None,
            "errors": [
                {
                    "message": "Throws!",
                    "locations": [{"line": 1, "column": 2}],
                    "path": ["error"],
                }
            ],
        }
    ]


def test_handles_syntax_errors_caught_by_graphql():
    results, params = run_http_query(schema, "get", dict(query="syntaxerror"))

    assert as_dicts(results) == [
        {
            "errors": [
                {
                    "locations": [{"line": 1, "column": 1}],
                    "message": "Syntax Error GraphQL (1:1)"
                    ' Unexpected Name "syntaxerror"\n\n1: syntaxerror\n   ^\n',
                }
            ]
        }
    ]


def test_handles_errors_caused_by_a_lack_of_query():
    with raises(HttpQueryError) as exc_info:
        run_http_query(schema, "get", {})

    assert exc_info.value == HttpQueryError(400, "Must provide query string.")


def test_handles_errors_caused_by_invalid_query_type():
    results, params = run_http_query(schema, "get", dict(query=42))

    assert as_dicts(results) == [
        {"errors": [{"message": "The query must be a string"}]}
    ]


def test_handles_batch_correctly_if_is_disabled():
    with raises(HttpQueryError) as exc_info:
        run_http_query(schema, "post", [])

    assert exc_info.value == HttpQueryError(
        400, "Batch GraphQL requests are not enabled."
    )


def test_handles_incomplete_json_bodies():
    with raises(HttpQueryError) as exc_info:
        run_http_query(schema, "post", load_json_body('{"query":'))

    assert exc_info.value == HttpQueryError(400, "POST body sent invalid JSON.")


def test_handles_plain_post_text():
    with raises(HttpQueryError) as exc_info:
        run_http_query(schema, "post", {})

    assert exc_info.value == HttpQueryError(400, "Must provide query string.")


def test_handles_poorly_formed_variables():
    with raises(HttpQueryError) as exc_info:
        run_http_query(
            schema,
            "get",
            {},
            dict(
                query="query helloWho($who: String){ test(who: $who) }",
                variables="who:You",
            ),
        )

    assert exc_info.value == HttpQueryError(400, "Variables are invalid JSON.")


def test_handles_bad_schema():
    with raises(TypeError) as exc_info:
        # noinspection PyTypeChecker
        run_http_query("not a schema", "get", {"query": "{error}"})  # type: ignore

    msg = str(exc_info.value)
    assert msg == "Expected a GraphQL schema, but received 'not a schema'."


def test_handles_unsupported_http_methods():
    with raises(HttpQueryError) as exc_info:
        run_http_query(schema, "put", {})

    assert exc_info.value == HttpQueryError(
        405,
        "GraphQL only supports GET and POST requests.",
        headers={"Allow": "GET, POST"},
    )


def test_passes_request_into_request_context():
    results, params = run_http_query(
        schema, "get", {}, dict(query="{request}"), context_value={"q": "testing"}
    )

    assert as_dicts(results) == [{"data": {"request": "testing"}}]


def test_supports_pretty_printing_context():
    class Context:
        def __str__(self):
            return "CUSTOM CONTEXT"

    results, params = run_http_query(
        schema, "get", {}, dict(query="{context}"), context_value=Context()
    )

    assert as_dicts(results) == [{"data": {"context": "CUSTOM CONTEXT"}}]


def test_post_multipart_data():
    query = "mutation TestMutation { writeTest { test } }"
    results, params = run_http_query(schema, "post", {}, query_data=dict(query=query))

    assert as_dicts(results) == [{"data": {"writeTest": {"test": "Hello World"}}}]


def test_batch_allows_post_with_json_encoding():
    data = load_json_body('[{"query": "{test}"}]')
    results, params = run_http_query(schema, "post", data, batch_enabled=True)

    assert as_dicts(results) == [{"data": {"test": "Hello World"}}]


def test_batch_supports_post_json_query_with_json_variables():
    data = load_json_body(
        '[{"query":"query helloWho($who: String){ test(who: $who) }",'
        '"variables":{"who":"Dolly"}}]'
    )
    results, params = run_http_query(schema, "post", data, batch_enabled=True)

    assert as_dicts(results) == [{"data": {"test": "Hello Dolly"}}]


def test_batch_allows_post_with_operation_name():
    data = [
        dict(
            query="""
            query helloYou { test(who: "You"), ...shared }
            query helloWorld { test(who: "World"), ...shared }
            query helloDolly { test(who: "Dolly"), ...shared }
            fragment shared on QueryRoot {
              shared: test(who: "Everyone")
            }
            """,
            operationName="helloWorld",
        )
    ]
    data = load_json_body(json_encode(data))
    results, params = run_http_query(schema, "post", data, batch_enabled=True)

    assert as_dicts(results) == [
        {"data": {"test": "Hello World", "shared": "Hello Everyone"}}
    ]


def test_get_responses_using_executor():
    class TestExecutor(object):
        called = False
        waited = False
        cleaned = False

        def wait_until_finished(self):
            TestExecutor.waited = True

        def clean(self):
            TestExecutor.cleaned = True

        def execute(self, fn, *args, **kwargs):
            TestExecutor.called = True
            return fn(*args, **kwargs)

    query = "{test}"
    results, params = run_http_query(
        schema, "get", {}, dict(query=query), executor=TestExecutor(),
    )

    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], ExecutionResult)

    assert as_dicts(results) == [{"data": {"test": "Hello World"}}]
    assert params == [RequestParams(query=query, variables=None, operation_name=None)]
    assert TestExecutor.called
    assert TestExecutor.waited
    assert not TestExecutor.cleaned


def test_get_responses_using_executor_return_promise():
    class TestExecutor(object):
        called = False
        waited = False
        cleaned = False

        def wait_until_finished(self):
            TestExecutor.waited = True

        def clean(self):
            TestExecutor.cleaned = True

        def execute(self, fn, *args, **kwargs):
            TestExecutor.called = True
            return fn(*args, **kwargs)

    query = "{test}"
    result_promises, params = run_http_query(
        schema,
        "get",
        {},
        dict(query=query),
        executor=TestExecutor(),
        return_promise=True,
    )

    assert isinstance(result_promises, list)
    assert len(result_promises) == 1
    assert isinstance(result_promises[0], Promise)
    results = Promise.all(result_promises).get()

    assert as_dicts(results) == [{"data": {"test": "Hello World"}}]
    assert params == [RequestParams(query=query, variables=None, operation_name=None)]
    assert TestExecutor.called
    assert not TestExecutor.waited
    assert TestExecutor.cleaned


def test_syntax_error_using_executor_return_promise():
    class TestExecutor(object):
        called = False
        waited = False
        cleaned = False

        def wait_until_finished(self):
            TestExecutor.waited = True

        def clean(self):
            TestExecutor.cleaned = True

        def execute(self, fn, *args, **kwargs):
            TestExecutor.called = True
            return fn(*args, **kwargs)

    query = "this is a syntax error"
    result_promises, params = run_http_query(
        schema,
        "get",
        {},
        dict(query=query),
        executor=TestExecutor(),
        return_promise=True,
    )

    assert isinstance(result_promises, list)
    assert len(result_promises) == 1
    assert isinstance(result_promises[0], Promise)
    results = Promise.all(result_promises).get()

    assert isinstance(results, list)
    assert len(results) == 1
    result = results[0]
    assert isinstance(result, ExecutionResult)

    assert result.data is None
    assert isinstance(result.errors, list)
    assert len(result.errors) == 1
    error = result.errors[0]
    assert isinstance(error, GraphQLSyntaxError)

    assert params == [RequestParams(query=query, variables=None, operation_name=None)]
    assert not TestExecutor.called
    assert not TestExecutor.waited
    assert not TestExecutor.cleaned
