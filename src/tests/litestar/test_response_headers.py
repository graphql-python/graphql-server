from graphql import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

from graphql_server.litestar import make_graphql_controller
from litestar import Litestar
from litestar.testing import TestClient


def test_set_response_headers():
    def resolve_abc(_root, info):
        assert info.context.get("response") is not None
        info.context["response"].headers["X-GraphQL-Server"] = "rocks"
        return "abc"

    Query = GraphQLObjectType(
        name="Query",
        fields={
            "abc": GraphQLField(
                GraphQLString,
                resolve=resolve_abc,
            )
        },
    )

    schema = GraphQLSchema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Litestar(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}
    assert response.headers["X-GraphQL-Server"] == "rocks"


def test_set_cookie_headers():
    def resolve_abc(_root, info):
        assert info.context.get("response") is not None
        info.context["response"].set_cookie(
            key="teststring",
            value="rocks",
        )
        info.context["response"].set_cookie(
            key="Litestar",
            value="rocks",
        )
        return "abc"

    Query = GraphQLObjectType(
        name="Query",
        fields={
            "abc": GraphQLField(
                GraphQLString,
                resolve=resolve_abc,
            )
        },
    )

    schema = GraphQLSchema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Litestar(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}
    assert response.headers["set-cookie"] == (
        "teststring=rocks; Path=/; SameSite=lax, Litestar=rocks; Path=/; SameSite=lax"
    )
