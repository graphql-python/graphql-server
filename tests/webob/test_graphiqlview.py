import pytest

from .app import Client, url_string


@pytest.fixture
def settings():
    return {}


@pytest.fixture
def client(settings):
    return Client(settings=settings)


@pytest.fixture
def pretty_response():
    return (
        "{\n"
        '  "data": {\n'
        '    "test": "Hello World"\n'
        "  }\n"
        "}".replace('"', '\\"').replace("\n", "\\n")
    )


@pytest.mark.parametrize("settings", [dict(graphiql=True)])
def test_graphiql_is_enabled(client, settings):
    response = client.get(url_string(query="{test}"), headers={"Accept": "text/html"})
    assert response.status_code == 200


@pytest.mark.parametrize("settings", [dict(graphiql=True)])
def test_graphiql_simple_renderer(client, settings, pretty_response):
    response = client.get(url_string(query="{test}"), headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert pretty_response in response.body.decode("utf-8")


@pytest.mark.parametrize("settings", [dict(graphiql=True)])
def test_graphiql_html_is_not_accepted(client, settings):
    response = client.get(url_string(), headers={"Accept": "application/json"})
    assert response.status_code == 400
