from __future__ import annotations

from typing import Optional

import pytest
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)
from starlette.testclient import TestClient

from tests.fastapi.app import create_app


async def resolve_hello(_root, _info, name: Optional[str] = None) -> str:
    return f"Hello {name or 'world'}"


QueryType = GraphQLObjectType(
    name="Query",
    fields={
        "hello": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={"name": GraphQLArgument(GraphQLString)},
            resolve=resolve_hello,
        )
    },
)


@pytest.fixture
def test_client() -> TestClient:
    schema = GraphQLSchema(query=QueryType)
    app = create_app(schema=schema)
    return TestClient(app)


def test_simple_query(test_client: TestClient):
    response = test_client.post("/graphql", json={"query": "{ hello }"})

    assert response.json() == {"data": {"hello": "Hello world"}}
