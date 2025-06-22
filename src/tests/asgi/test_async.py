from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

if TYPE_CHECKING:
    from starlette.testclient import TestClient


@pytest.fixture
def test_client() -> TestClient:
    from starlette.testclient import TestClient

    from graphql_server.asgi import GraphQL

    # Resolver ------------------------------------------------------
    async def resolve_hello(obj, info, name: str | None = None) -> str:
        return f"Hello {name or 'world'}"

    # Root "Query" type --------------------------------------------
    QueryType = GraphQLObjectType(
        name="Query",
        fields={
            "hello": GraphQLField(
                type_=GraphQLString,  # → String!
                args={"name": GraphQLArgument(GraphQLString)},  # Optional by default
                resolve=resolve_hello,
            )
        },
    )

    # Final schema --------------------------------------------------
    schema: GraphQLSchema = GraphQLSchema(query=QueryType)
    app = GraphQL[None, None](schema)
    return TestClient(app)


def test_simple_query(test_client: TestClient):
    response = test_client.post("/", json={"query": "{ hello }"})
    print(response.text)
    assert response.json() == {"data": {"hello": "Hello world"}}
