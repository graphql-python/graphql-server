from urllib.parse import quote
from typing import Union
from typing_extensions import Literal

import pytest

from .clients.base import HttpClient


@pytest.mark.parametrize(
    "header_value",
    [
        "text/html",
    ],
)
@pytest.mark.parametrize(
    "graphql_ide_and_title",
    [
        ("graphiql", "GraphiQL"),
        ("apollo-sandbox", "Apollo Sandbox"),
        ("pathfinder", "GraphQL Pathfinder"),
    ],
)
async def test_renders_graphql_ide(
    header_value: str,
    http_client_class: type[HttpClient],
    graphql_ide_and_title: tuple[Literal["graphiql"], Literal["GraphiQL"]]
    | tuple[Literal["apollo-sandbox"], Literal["Apollo Sandbox"]]
    | tuple[Literal["pathfinder"], Literal["GraphQL Pathfinder"]],
):
    graphql_ide, title = graphql_ide_and_title
    http_client = http_client_class(graphql_ide=graphql_ide)

    response = await http_client.get("/graphql", headers={"Accept": header_value})
    content_type = response.headers.get(
        "content-type", response.headers.get("Content-Type", "")
    )

    assert response.status_code == 200
    assert "text/html" in content_type
    assert f"<title>{title}</title>" in response.text

    if graphql_ide == "apollo-sandbox":
        assert "embeddable-sandbox.cdn.apollographql" in response.text

    if graphql_ide == "pathfinder":
        assert "@pathfinder-ide/react" in response.text

    if graphql_ide == "graphiql":
        assert "unpkg.com/graphiql" in response.text


@pytest.mark.parametrize(
    "header_value",
    [
        "text/html",
    ],
)
async def test_renders_graphql_ide_deprecated(
    header_value: str, http_client_class: type[HttpClient]
):
    with pytest.deprecated_call(
        match=r"The `graphiql` argument is deprecated in favor of `graphql_ide`"
    ):
        http_client = http_client_class(graphiql=True)

        response = await http_client.get("/graphql", headers={"Accept": header_value})

    content_type = response.headers.get(
        "content-type", response.headers.get("Content-Type", "")
    )

    assert response.status_code == 200
    assert "text/html" in content_type
    assert "<title>GraphiQL</title>" in response.text

    assert "https://unpkg.com/graphiql" in response.text


async def test_does_not_render_graphiql_if_wrong_accept(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class()
    response = await http_client.get("/graphql", headers={"Accept": "text/xml"})

    assert response.status_code != 200


@pytest.mark.parametrize("graphql_ide", [False, None])
async def test_renders_graphiql_disabled(
    http_client_class: type[HttpClient],
    graphql_ide: Union[bool, None],
):
    http_client = http_client_class(graphql_ide=graphql_ide)
    response = await http_client.get("/graphql", headers={"Accept": "text/html"})

    assert response.status_code != 200


async def test_renders_graphiql_disabled_deprecated(
    http_client_class: type[HttpClient],
):
    with pytest.deprecated_call(
        match=r"The `graphiql` argument is deprecated in favor of `graphql_ide`"
    ):
        http_client = http_client_class(graphiql=False)
        response = await http_client.get("/graphql", headers={"Accept": "text/html"})

    assert response.status_code != 200


@pytest.mark.parametrize(
    "header_value",
    [
        "text/html",
    ],
)
@pytest.mark.parametrize(
    "graphql_ide_and_title",
    [
        ("graphiql", "GraphiQL"),
        # ("apollo-sandbox", "Apollo Sandbox"),
        # ("pathfinder", "GraphQL Pathfinder"),
    ],
)
async def test_renders_graphql_ide_with_variables(
    header_value: str,
    http_client_class: type[HttpClient],
    graphql_ide_and_title: tuple[Literal["graphiql"], Literal["GraphiQL"]]
    | tuple[Literal["apollo-sandbox"], Literal["Apollo Sandbox"]]
    | tuple[Literal["pathfinder"], Literal["GraphQL Pathfinder"]],
):
    graphql_ide, title = graphql_ide_and_title
    http_client = http_client_class(graphql_ide=graphql_ide)

    query = "query { __typename }"
    query_encoded = quote(query)
    response = await http_client.get(
        f"/graphql?query={query_encoded}", headers={"Accept": header_value}
    )
    content_type = response.headers.get(
        "content-type", response.headers.get("Content-Type", "")
    )

    assert response.status_code == 200
    assert "text/html" in content_type
    assert f"<title>{title}</title>" in response.text
    assert "__typename" in response.text

    if graphql_ide == "apollo-sandbox":
        assert "embeddable-sandbox.cdn.apollographql" in response.text

    if graphql_ide == "pathfinder":
        assert "@pathfinder-ide/react" in response.text

    if graphql_ide == "graphiql":
        assert "unpkg.com/graphiql" in response.text
