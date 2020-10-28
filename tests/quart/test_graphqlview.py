import json
import sys

# from io import StringIO
from urllib.parse import urlencode

import pytest
from quart import Quart, Response, url_for
from quart.testing import QuartClient
from werkzeug.datastructures import Headers

from .app import create_app


@pytest.fixture
def app() -> Quart:
    # import app factory pattern
    app = create_app(graphiql=True)

    # pushes an application context manually
    # ctx = app.app_context()
    # await ctx.push()
    return app


@pytest.fixture
def client(app: Quart) -> QuartClient:
    return app.test_client()


@pytest.mark.asyncio
async def execute_client(
    app: Quart,
    client: QuartClient,
    method: str = "GET",
    data: str = None,
    headers: Headers = None,
    **url_params
) -> Response:
    if sys.version_info >= (3, 7):
        test_request_context = app.test_request_context("/", method=method)
    else:
        test_request_context = app.test_request_context(method, "/")
    async with test_request_context:
        string = url_for("graphql")

    if url_params:
        string += "?" + urlencode(url_params)

    if method == "POST":
        return await client.post(string, data=data, headers=headers)
    elif method == "PUT":
        return await client.put(string, data=data, headers=headers)
    else:
        return await client.get(string)


def response_json(result):
    return json.loads(result)


def json_dump_kwarg(**kwargs) -> str:
    return json.dumps(kwargs)


def json_dump_kwarg_list(**kwargs):
    return json.dumps([kwargs])


@pytest.mark.asyncio
async def test_allows_get_with_query_param(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{test}")

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello World"}}


@pytest.mark.asyncio
async def test_allows_get_with_variable_values(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        query="query helloWho($who: String){ test(who: $who) }",
        variables=json.dumps({"who": "Dolly"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello Dolly"}}


@pytest.mark.asyncio
async def test_allows_get_with_operation_name(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
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

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "data": {"test": "Hello World", "shared": "Hello Everyone"}
    }


@pytest.mark.asyncio
async def test_reports_validation_errors(app: Quart, client: QuartClient):
    response = await execute_client(
        app, client, query="{ test, unknownOne, unknownTwo }"
    )

    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {
                "message": "Cannot query field 'unknownOne' on type 'QueryRoot'.",
                "locations": [{"line": 1, "column": 9}],
                "path": None,
            },
            {
                "message": "Cannot query field 'unknownTwo' on type 'QueryRoot'.",
                "locations": [{"line": 1, "column": 21}],
                "path": None,
            },
        ]
    }


@pytest.mark.asyncio
async def test_errors_when_missing_operation_name(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        query="""
            query TestQuery { test }
            mutation TestMutation { writeTest { test } }
        """,
    )

    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {
                "message": "Must provide operation name if query contains multiple operations.",  # noqa: E501
                "locations": None,
                "path": None,
            }
        ]
    }


@pytest.mark.asyncio
async def test_errors_when_sending_a_mutation_via_get(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        query="""
            mutation TestMutation { writeTest { test } }
        """,
    )
    assert response.status_code == 405
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {
                "message": "Can only perform a mutation operation from a POST request.",
                "locations": None,
                "path": None,
            }
        ]
    }


@pytest.mark.asyncio
async def test_errors_when_selecting_a_mutation_within_a_get(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client,
        query="""
            query TestQuery { test }
            mutation TestMutation { writeTest { test } }
        """,
        operationName="TestMutation",
    )

    assert response.status_code == 405
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {
                "message": "Can only perform a mutation operation from a POST request.",
                "locations": None,
                "path": None,
            }
        ]
    }


@pytest.mark.asyncio
async def test_allows_mutation_to_exist_within_a_get(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        query="""
            query TestQuery { test }
            mutation TestMutation { writeTest { test } }
        """,
        operationName="TestQuery",
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello World"}}


@pytest.mark.asyncio
async def test_allows_post_with_json_encoding(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg(query="{test}"),
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello World"}}


@pytest.mark.asyncio
async def test_allows_sending_a_mutation_via_post(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg(query="mutation TestMutation { writeTest { test } }"),
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"writeTest": {"test": "Hello World"}}}


@pytest.mark.asyncio
async def test_allows_post_with_url_encoding(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=urlencode(dict(query="{test}")),
        headers=Headers({"Content-Type": "application/x-www-form-urlencoded"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello World"}}


@pytest.mark.asyncio
async def test_supports_post_json_query_with_string_variables(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg(
            query="query helloWho($who: String){ test(who: $who) }",
            variables=json.dumps({"who": "Dolly"}),
        ),
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello Dolly"}}


@pytest.mark.asyncio
async def test_supports_post_json_query_with_json_variables(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg(
            query="query helloWho($who: String){ test(who: $who) }",
            variables={"who": "Dolly"},
        ),
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello Dolly"}}


@pytest.mark.asyncio
async def test_supports_post_url_encoded_query_with_string_variables(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=urlencode(
            dict(
                query="query helloWho($who: String){ test(who: $who) }",
                variables=json.dumps({"who": "Dolly"}),
            )
        ),
        headers=Headers({"Content-Type": "application/x-www-form-urlencoded"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello Dolly"}}


@pytest.mark.asyncio
async def test_supports_post_json_query_with_get_variable_values(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg(query="query helloWho($who: String){ test(who: $who) }",),
        headers=Headers({"Content-Type": "application/json"}),
        variables=json.dumps({"who": "Dolly"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello Dolly"}}


@pytest.mark.asyncio
async def test_post_url_encoded_query_with_get_variable_values(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=urlencode(dict(query="query helloWho($who: String){ test(who: $who) }",)),
        headers=Headers({"Content-Type": "application/x-www-form-urlencoded"}),
        variables=json.dumps({"who": "Dolly"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello Dolly"}}


@pytest.mark.asyncio
async def test_supports_post_raw_text_query_with_get_variable_values(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client=client,
        method="POST",
        data="query helloWho($who: String){ test(who: $who) }",
        headers=Headers({"Content-Type": "application/graphql"}),
        variables=json.dumps({"who": "Dolly"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"test": "Hello Dolly"}}


@pytest.mark.asyncio
async def test_allows_post_with_operation_name(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg(
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
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "data": {"test": "Hello World", "shared": "Hello Everyone"}
    }


@pytest.mark.asyncio
async def test_allows_post_with_get_operation_name(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data="""
            query helloYou { test(who: "You"), ...shared }
            query helloWorld { test(who: "World"), ...shared }
            query helloDolly { test(who: "Dolly"), ...shared }
            fragment shared on QueryRoot {
              shared: test(who: "Everyone")
            }
        """,
        headers=Headers({"Content-Type": "application/graphql"}),
        operationName="helloWorld",
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "data": {"test": "Hello World", "shared": "Hello Everyone"}
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(pretty=True)])
async def test_supports_pretty_printing(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{test}")

    result = await response.get_data(raw=False)
    assert result == ("{\n" '  "data": {\n' '    "test": "Hello World"\n' "  }\n" "}")


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(pretty=False)])
async def test_not_pretty_by_default(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{test}")

    result = await response.get_data(raw=False)
    assert result == '{"data":{"test":"Hello World"}}'


@pytest.mark.asyncio
async def test_supports_pretty_printing_by_request(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{test}", pretty="1")

    result = await response.get_data(raw=False)
    assert result == ("{\n" '  "data": {\n' '    "test": "Hello World"\n' "  }\n" "}")


@pytest.mark.asyncio
async def test_handles_field_errors_caught_by_graphql(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{thrower}")
    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {
                "locations": [{"column": 2, "line": 1}],
                "path": ["thrower"],
                "message": "Throws!",
            }
        ],
        "data": None,
    }


@pytest.mark.asyncio
async def test_handles_syntax_errors_caught_by_graphql(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="syntaxerror")
    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {
                "locations": [{"column": 1, "line": 1}],
                "message": "Syntax Error: Unexpected Name 'syntaxerror'.",
                "path": None,
            }
        ]
    }


@pytest.mark.asyncio
async def test_handles_errors_caused_by_a_lack_of_query(
    app: Quart, client: QuartClient
):
    response = await execute_client(app, client)

    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {"message": "Must provide query string.", "locations": None, "path": None}
        ]
    }


@pytest.mark.asyncio
async def test_handles_batch_correctly_if_is_disabled(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data="[]",
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {
                "message": "Batch GraphQL requests are not enabled.",
                "locations": None,
                "path": None,
            }
        ]
    }


@pytest.mark.asyncio
async def test_handles_incomplete_json_bodies(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data='{"query":',
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {"message": "POST body sent invalid JSON.", "locations": None, "path": None}
        ]
    }


@pytest.mark.asyncio
async def test_handles_plain_post_text(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data="query helloWho($who: String){ test(who: $who) }",
        headers=Headers({"Content-Type": "text/plain"}),
        variables=json.dumps({"who": "Dolly"}),
    )
    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {"message": "Must provide query string.", "locations": None, "path": None}
        ]
    }


@pytest.mark.asyncio
async def test_handles_poorly_formed_variables(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        query="query helloWho($who: String){ test(who: $who) }",
        variables="who:You",
    )
    assert response.status_code == 400
    result = await response.get_data(raw=False)
    assert response_json(result) == {
        "errors": [
            {"message": "Variables are invalid JSON.", "locations": None, "path": None}
        ]
    }


@pytest.mark.asyncio
async def test_handles_unsupported_http_methods(app: Quart, client: QuartClient):
    response = await execute_client(app, client, method="PUT", query="{test}")
    assert response.status_code == 405
    result = await response.get_data(raw=False)
    assert response.headers["Allow"] in ["GET, POST", "HEAD, GET, POST, OPTIONS"]
    assert response_json(result) == {
        "errors": [
            {
                "message": "GraphQL only supports GET and POST requests.",
                "locations": None,
                "path": None,
            }
        ]
    }


@pytest.mark.asyncio
async def test_passes_request_into_request_context(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{request}", q="testing")

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == {"data": {"request": "testing"}}


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(context={"session": "CUSTOM CONTEXT"})])
async def test_passes_custom_context_into_context(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{context { session request }}")

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    res = response_json(result)
    assert "data" in res
    assert "session" in res["data"]["context"]
    assert "request" in res["data"]["context"]
    assert "CUSTOM CONTEXT" in res["data"]["context"]["session"]
    assert "Request" in res["data"]["context"]["request"]


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(context="CUSTOM CONTEXT")])
async def test_context_remapped_if_not_mapping(app: Quart, client: QuartClient):
    response = await execute_client(app, client, query="{context { session request }}")

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    res = response_json(result)
    assert "data" in res
    assert "session" in res["data"]["context"]
    assert "request" in res["data"]["context"]
    assert "CUSTOM CONTEXT" not in res["data"]["context"]["request"]
    assert "Request" in res["data"]["context"]["request"]


# @pytest.mark.asyncio
# async def test_post_multipart_data(app: Quart, client: QuartClient):
#     query = "mutation TestMutation { writeTest { test } }"
#     response = await execute_client(
#         app,
#         client,
#         method='POST',
#         data={"query": query, "file": (StringIO(), "text1.txt")},
#         headers=Headers({"Content-Type": "multipart/form-data"})
#     )
#
#     assert response.status_code == 200
#     result = await response.get_data()
#     assert response_json(result) == {
#         "data": {u"writeTest": {u"test": u"Hello World"}}
#     }


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(batch=True)])
async def test_batch_allows_post_with_json_encoding(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg_list(query="{test}"),
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == [{"data": {"test": "Hello World"}}]


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(batch=True)])
async def test_batch_supports_post_json_query_with_json_variables(
    app: Quart, client: QuartClient
):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg_list(
            query="query helloWho($who: String){ test(who: $who) }",
            variables={"who": "Dolly"},
        ),
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == [{"data": {"test": "Hello Dolly"}}]


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(batch=True)])
async def test_batch_allows_post_with_operation_name(app: Quart, client: QuartClient):
    response = await execute_client(
        app,
        client,
        method="POST",
        data=json_dump_kwarg_list(
            # id=1,
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
        headers=Headers({"Content-Type": "application/json"}),
    )

    assert response.status_code == 200
    result = await response.get_data(raw=False)
    assert response_json(result) == [
        {"data": {"test": "Hello World", "shared": "Hello Everyone"}}
    ]
