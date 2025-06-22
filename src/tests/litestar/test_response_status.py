from graphql import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

from graphql_server.litestar import make_graphql_controller
from litestar import Litestar
from litestar.testing import TestClient


def test_set_custom_http_response_status():
    def resolve_abc(_root, info):
        assert info.context.get("response") is not None
        info.context["response"].status_code = 418
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
    assert response.status_code == 418
    assert response.json() == {"data": {"abc": "abc"}}


def test_set_without_setting_http_response_status():
    def resolve_abc(_root, _info):
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
