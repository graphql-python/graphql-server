import pytest
from aiohttp.test_utils import TestClient, TestServer
from jinja2 import Environment

from tests.aiohttp.app import create_app, url_string
from tests.aiohttp.schema import AsyncSchema, Schema, SyncSchema


@pytest.fixture
def app():
    app = create_app()
    return app


@pytest.fixture
async def client(app):
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()


@pytest.fixture
def view_kwargs():
    return {
        "schema": Schema,
        "graphiql": True,
    }


@pytest.fixture
def pretty_response():
    return (
        "{\n"
        '  "data": {\n'
        '    "test": "Hello World"\n'
        "  }\n"
        "}".replace('"', '\\"').replace("\n", "\\n")
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(graphiql=True)])
async def test_graphiql_is_enabled(app, client):
    response = await client.get(
        url_string(query="{test}"), headers={"Accept": "text/html"}
    )
    assert response.status == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(graphiql=True)])
async def test_graphiql_simple_renderer(app, client, pretty_response):
    response = await client.get(
        url_string(query="{test}"), headers={"Accept": "text/html"},
    )
    assert response.status == 200
    assert pretty_response in await response.text()


class TestJinjaEnv:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "app", [create_app(graphiql=True, jinja_env=Environment(enable_async=True))]
    )
    async def test_graphiql_jinja_renderer_async(self, app, client, pretty_response):
        response = await client.get(
            url_string(query="{test}"), headers={"Accept": "text/html"},
        )
        assert response.status == 200
        assert pretty_response in await response.text()


@pytest.mark.asyncio
async def test_graphiql_html_is_not_accepted(client):
    response = await client.get("/graphql", headers={"Accept": "application/json"},)
    assert response.status == 400


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(graphiql=True)])
async def test_graphiql_get_mutation(app, client):
    response = await client.get(
        url_string(query="mutation TestMutation { writeTest { test } }"),
        headers={"Accept": "text/html"},
    )
    assert response.status == 200
    assert "response: null" in await response.text()


@pytest.mark.asyncio
@pytest.mark.parametrize("app", [create_app(graphiql=True)])
async def test_graphiql_get_subscriptions(app, client):
    response = await client.get(
        url_string(
            query="subscription TestSubscriptions { subscriptionsTest { test } }"
        ),
        headers={"Accept": "text/html"},
    )
    assert response.status == 200
    assert "response: null" in await response.text()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "app", [create_app(schema=AsyncSchema, enable_async=True, graphiql=True)]
)
async def test_graphiql_enabled_async_schema(app, client):
    response = await client.get(
        url_string(query="{a,b,c}"), headers={"Accept": "text/html"},
    )

    expected_response = (
        (
            "{\n"
            '  "data": {\n'
            '    "a": "hey",\n'
            '    "b": "hey2",\n'
            '    "c": "hey3"\n'
            "  }\n"
            "}"
        )
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    assert response.status == 200
    assert expected_response in await response.text()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "app", [create_app(schema=SyncSchema, enable_async=True, graphiql=True)]
)
async def test_graphiql_enabled_sync_schema(app, client):
    response = await client.get(
        url_string(query="{a,b}"), headers={"Accept": "text/html"},
    )

    expected_response = (
        (
            "{\n"
            '  "data": {\n'
            '    "a": "synced_one",\n'
            '    "b": "synced_two"\n'
            "  }\n"
            "}"
        )
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    assert response.status == 200
    assert expected_response in await response.text()
