import pytest
from graphql import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString


def resolve_abc(_root, _info) -> str:
    return "abc"


def test_include_router_prefix():
    from starlette.testclient import TestClient

    from fastapi import FastAPI
    from graphql_server.fastapi import GraphQLRouter

    QueryType = GraphQLObjectType(
        name="Query",
        fields={"abc": GraphQLField(GraphQLString, resolve=resolve_abc)},
    )

    app = FastAPI()
    schema = GraphQLSchema(query=QueryType)
    graphql_app = GraphQLRouter[None, None](schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_graphql_router_path():
    from starlette.testclient import TestClient

    from fastapi import FastAPI
    from graphql_server.fastapi import GraphQLRouter

    QueryType = GraphQLObjectType(
        name="Query",
        fields={"abc": GraphQLField(GraphQLString, resolve=resolve_abc)},
    )

    app = FastAPI()
    schema = GraphQLSchema(query=QueryType)
    graphql_app = GraphQLRouter[None, None](schema, path="/graphql")
    app.include_router(graphql_app)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_missing_path_and_prefix():
    from fastapi import FastAPI
    from graphql_server.fastapi import GraphQLRouter

    QueryType = GraphQLObjectType(
        name="Query",
        fields={"abc": GraphQLField(GraphQLString, resolve=resolve_abc)},
    )

    app = FastAPI()
    schema = GraphQLSchema(query=QueryType)
    graphql_app = GraphQLRouter[None, None](schema)

    with pytest.raises(Exception) as exc:
        app.include_router(graphql_app)

    assert "Prefix and path cannot be both empty" in str(exc)
