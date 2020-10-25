import pytest
from quart import Quart, url_for
from quart.testing import QuartClient

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
async def test_graphiql_is_enabled(app: Quart, client: QuartClient):
    async with app.test_request_context("/", method="GET"):
        response = await client.get(
            url_for("graphql", externals=False), headers={"Accept": "text/html"}
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_graphiql_renders_pretty(app: Quart, client: QuartClient):
    async with app.test_request_context("/", method="GET"):
        response = await client.get(
            url_for("graphql", query="{test}"), headers={"Accept": "text/html"}
        )
    assert response.status_code == 200
    pretty_response = (
        "{\n"
        '  "data": {\n'
        '    "test": "Hello World"\n'
        "  }\n"
        "}".replace('"', '\\"').replace("\n", "\\n")
    )
    result = await response.get_data(raw=False)
    assert pretty_response in result


@pytest.mark.asyncio
async def test_graphiql_default_title(app: Quart, client: QuartClient):
    async with app.test_request_context("/", method="GET"):
        response = await client.get(url_for("graphql"), headers={"Accept": "text/html"})
    result = await response.get_data(raw=False)
    assert "<title>GraphiQL</title>" in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "app", [create_app(graphiql=True, graphiql_html_title="Awesome")]
)
async def test_graphiql_custom_title(app: Quart, client: QuartClient):
    async with app.test_request_context("/", method="GET"):
        response = await client.get(url_for("graphql"), headers={"Accept": "text/html"})
    result = await response.get_data(raw=False)
    assert "<title>Awesome</title>" in result
