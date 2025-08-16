import asyncio
from collections.abc import AsyncGenerator

import pytest
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLFloat,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)


def test_base_context():
    from graphql_server.fastapi import BaseContext

    base_context = BaseContext()
    assert base_context.request is None
    assert base_context.background_tasks is None
    assert base_context.response is None


def test_with_explicit_class_context_getter():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from graphql_server.fastapi import BaseContext, GraphQLRouter

    class CustomContext(BaseContext):
        def __init__(self, rocks: str):
            self.graphql_server = rocks

    def custom_context_dependency() -> CustomContext:
        return CustomContext(rocks="explicitly rocks")

    def get_context(custom_context: CustomContext = Depends(custom_context_dependency)):
        return custom_context

    async def resolve_abc(_root, info) -> str:
        assert info.context.request is not None
        assert info.context.graphql_server == "explicitly rocks"
        assert info.context.connection_params is None
        return "abc"

    QueryType = GraphQLObjectType(
        name="Query",
        fields={
            "abc": GraphQLField(
                GraphQLString,
                resolve=resolve_abc,
            )
        },
    )

    app = FastAPI()
    schema = GraphQLSchema(query=QueryType)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_implicit_class_context_getter():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from graphql_server.fastapi import BaseContext, GraphQLRouter

    class CustomContext(BaseContext):
        def __init__(self, rocks: str = "implicitly rocks"):
            super().__init__()
            self.graphql_server = rocks

    def get_context(context: CustomContext = Depends()):
        return context

    async def resolve_abc(_root, info) -> str:
        assert info.context.request is not None
        assert info.context.graphql_server == "implicitly rocks"
        assert info.context.connection_params is None
        return "abc"

    app = FastAPI()
    QueryType = GraphQLObjectType(
        name="Query",
        fields={
            "abc": GraphQLField(
                GraphQLString,
                resolve=resolve_abc,
            )
        },
    )

    schema = GraphQLSchema(query=QueryType)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_dict_context_getter():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from graphql_server.fastapi import GraphQLRouter

    def custom_context_dependency() -> str:
        return "rocks"

    def get_context(value: str = Depends(custom_context_dependency)) -> dict[str, str]:
        return {"graphql_server": value}

    async def resolve_abc(_root, info) -> str:
        assert info.context.get("request") is not None
        assert "connection_params" not in info.context
        assert info.context.get("graphql_server") == "rocks"
        return "abc"

    app = FastAPI()
    QueryType = GraphQLObjectType(
        name="Query",
        fields={
            "abc": GraphQLField(
                GraphQLString,
                resolve=resolve_abc,
            )
        },
    )

    schema = GraphQLSchema(query=QueryType)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_without_context_getter():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from graphql_server.fastapi import GraphQLRouter

    async def resolve_abc(_root, info) -> str:
        assert info.context.get("request") is not None
        assert info.context.get("graphql_server") is None
        return "abc"

    app = FastAPI()
    QueryType = GraphQLObjectType(
        name="Query",
        fields={
            "abc": GraphQLField(
                GraphQLString,
                resolve=resolve_abc,
            )
        },
    )

    schema = GraphQLSchema(query=QueryType)
    graphql_app = GraphQLRouter(schema=schema, context_getter=None)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_class_context_injects_connection_params_over_transport_ws():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from graphql_server.fastapi import BaseContext, GraphQLRouter
    from graphql_server.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
    from graphql_server.subscriptions.protocols.graphql_transport_ws import (
        types as transport_ws_types,
    )

    # Resolver for the Subscription.connectionParams field
    async def subscribe_connection_params(
        _root, info, delay: float = 0
    ) -> AsyncGenerator[str, None]:
        assert info.context.request is not None
        await asyncio.sleep(delay)
        yield info.context.connection_params["graphql_server"]

    QueryType = GraphQLObjectType(
        name="Query",
        fields={
            "x": GraphQLField(
                GraphQLString,
                resolve=lambda _root, _info: "hi",
            )
        },
    )

    # Subscription type (replacing @graphql_server.type class Subscription)
    SubscriptionType = GraphQLObjectType(
        name="Subscription",
        fields={
            "connectionParams": GraphQLField(
                GraphQLString,
                args={"delay": GraphQLArgument(GraphQLFloat)},
                subscribe=subscribe_connection_params,
                resolve=lambda payload, *args, **kwargs: payload,
            )
        },
    )

    class Context(BaseContext):
        graphql_server: str

        def __init__(self):
            self.graphql_server = "rocks"

    def get_context(context: Context = Depends()) -> Context:
        return context

    app = FastAPI()

    QueryType = GraphQLObjectType(
        name="Query",
        fields={"x": GraphQLField(GraphQLString, resolve=lambda *_: "hi")},
    )

    async def subscribe_connection_params(_root, info, delay: float = 0):
        assert info.context.request is not None
        await asyncio.sleep(delay)
        yield info.context.connection_params["graphql_server"]

    SubscriptionType = GraphQLObjectType(
        name="Subscription",
        fields={
            "connectionParams": GraphQLField(
                GraphQLString,
                args={"delay": GraphQLArgument(GraphQLFloat)},
                subscribe=subscribe_connection_params,
                resolve=lambda payload, *args, **kwargs: payload,
            )
        },
    )

    schema = GraphQLSchema(query=QueryType, subscription=SubscriptionType)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(
            transport_ws_types.ConnectionInitMessage(
                {"type": "connection_init", "payload": {"graphql_server": "rocks"}}
            )
        )

        connection_ack_message = ws.receive_json()
        assert connection_ack_message == {"type": "connection_ack"}

        ws.send_json(
            transport_ws_types.SubscribeMessage(
                {
                    "id": "sub1",
                    "type": "subscribe",
                    "payload": {"query": "subscription { connectionParams }"},
                }
            )
        )

        next_message = ws.receive_json()
        assert next_message == {
            "id": "sub1",
            "type": "next",
            "payload": {"data": {"connectionParams": "rocks"}},
        }

        ws.send_json(
            transport_ws_types.CompleteMessage({"id": "sub1", "type": "complete"})
        )

        ws.close()


def test_class_context_injects_connection_params_over_ws():
    from starlette.websockets import WebSocketDisconnect

    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from graphql_server.fastapi import BaseContext, GraphQLRouter
    from graphql_server.subscriptions import GRAPHQL_WS_PROTOCOL
    from graphql_server.subscriptions.protocols.graphql_ws import types as ws_types

    class Context(BaseContext):
        graphql_server: str

        def __init__(self):
            self.graphql_server = "rocks"

    def get_context(context: Context = Depends()) -> Context:
        return context

    app = FastAPI()

    QueryType = GraphQLObjectType(
        name="Query",
        fields={"x": GraphQLField(GraphQLString, resolve=lambda *_: "hi")},
    )

    async def subscribe_connection_params(_root, info, delay: float = 0):
        assert info.context.request is not None
        await asyncio.sleep(delay)
        yield info.context.connection_params["graphql_server"]

    SubscriptionType = GraphQLObjectType(
        name="Subscription",
        fields={
            "connectionParams": GraphQLField(
                GraphQLString,
                args={"delay": GraphQLArgument(GraphQLFloat)},
                subscribe=subscribe_connection_params,
                resolve=lambda payload, *args, **kwargs: payload,
            )
        },
    )

    schema = GraphQLSchema(query=QueryType, subscription=SubscriptionType)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    with test_client.websocket_connect("/graphql", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json(
            ws_types.ConnectionInitMessage(
                {"type": "connection_init", "payload": {"graphql_server": "rocks"}}
            )
        )
        ws.send_json(
            ws_types.StartMessage(
                {
                    "type": "start",
                    "id": "demo",
                    "payload": {
                        "query": "subscription { connectionParams }",
                    },
                }
            )
        )

        connection_ack_message = ws.receive_json()
        assert connection_ack_message["type"] == "connection_ack"

        data_message = ws.receive_json()
        assert data_message["type"] == "data"
        assert data_message["id"] == "demo"
        assert data_message["payload"]["data"] == {"connectionParams": "rocks"}

        ws.send_json(ws_types.StopMessage({"type": "stop", "id": "demo"}))

        complete_message = ws.receive_json()
        assert complete_message["type"] == "complete"
        assert complete_message["id"] == "demo"

        ws.send_json(
            ws_types.ConnectionTerminateMessage({"type": "connection_terminate"})
        )

        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()
