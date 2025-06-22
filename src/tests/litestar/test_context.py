import pytest
from graphql import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

from graphql_server.litestar import BaseContext, make_graphql_controller
from litestar import Litestar
from litestar.di import Provide
from litestar.testing import TestClient


def test_base_context():
    base_context = BaseContext()
    assert base_context.request is None


def test_with_class_context_getter():
    class CustomContext(BaseContext):
        teststring: str

    def custom_context_dependency() -> CustomContext:
        return CustomContext(teststring="rocks")

    async def get_context(custom_context_dependency: CustomContext):
        return custom_context_dependency

    def resolve_abc(_root, info):
        assert isinstance(info.context, CustomContext)
        assert info.context.request is not None
        assert info.context.teststring == "rocks"
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
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Litestar(
        route_handlers=[graphql_controller],
        dependencies={
            "custom_context_dependency": Provide(
                custom_context_dependency, sync_to_thread=True
            )
        },
    )

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_dict_context_getter():
    def custom_context_dependency() -> str:
        return "rocks"

    async def get_context(custom_context_dependency: str) -> dict[str, str]:
        return {"teststring": custom_context_dependency}

    def resolve_abc(_root, info):
        assert isinstance(info.context, dict)
        assert info.context.get("request") is not None
        assert info.context.get("teststring") == "rocks"
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
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Litestar(
        route_handlers=[graphql_controller],
        dependencies={
            "custom_context_dependency": Provide(
                custom_context_dependency, sync_to_thread=True
            )
        },
    )
    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_without_context_getter():
    def resolve_abc(_root, info):
        assert isinstance(info.context, dict)
        assert info.context.get("request") is not None
        assert info.context.get("teststring") is None
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
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=None
    )
    app = Litestar(route_handlers=[graphql_controller])
    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


@pytest.mark.skip(reason="This is no longer supported")
def test_with_invalid_context_getter():
    def custom_context_dependency() -> str:
        return "rocks"

    async def get_context(custom_context_dependency: str) -> str:
        return custom_context_dependency

    def resolve_abc(_root, info):
        assert info.context.get("request") is not None
        assert info.context.get("teststring") is None
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
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Litestar(
        route_handlers=[graphql_controller],
        dependencies={
            "custom_context_dependency": Provide(
                custom_context_dependency, sync_to_thread=True
            )
        },
    )
    test_client = TestClient(app, raise_server_exceptions=True)
    response = test_client.post("/graphql", json={"query": "{ abc }"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal Server Error"


def test_custom_context():
    from tests.litestar.app import create_app

    def resolve_custom_context_value(_root, info):
        return info.context["custom_value"]

    Query = GraphQLObjectType(
        name="Query",
        fields={
            "customContextValue": GraphQLField(
                GraphQLString,
                resolve=resolve_custom_context_value,
            )
        },
    )

    schema = GraphQLSchema(query=Query)
    app = create_app(schema=schema)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ customContextValue }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"customContextValue": "Hi!"}}


def test_can_set_background_task():
    from tests.litestar.app import create_app

    task_complete = False

    async def task():
        nonlocal task_complete
        task_complete = True

    def resolve_something(_root, info):
        response = info.context["response"]
        response.background.tasks.append(task)
        return "foo"

    Query = GraphQLObjectType(
        name="Query",
        fields={
            "something": GraphQLField(
                GraphQLString,
                resolve=resolve_something,
            )
        },
    )

    schema = GraphQLSchema(query=Query)
    app = create_app(schema=schema)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ something }"})

    assert response.json() == {"data": {"something": "foo"}}
    assert task_complete
