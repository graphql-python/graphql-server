import asyncio
import contextlib

from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLError,
    GraphQLField,
    GraphQLFloat,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
)
from graphql.language import ast

from graphql_server.file_uploads import Upload as UploadValue


def _read_file(text_file: UploadValue) -> str:
    with contextlib.suppress(ModuleNotFoundError):
        from starlette.datastructures import UploadFile as StarletteUploadFile

        if isinstance(text_file, StarletteUploadFile):
            text_file = text_file.file._file  # type: ignore

    with contextlib.suppress(ModuleNotFoundError):
        from litestar.datastructures import UploadFile as LitestarUploadFile

        if isinstance(text_file, LitestarUploadFile):
            text_file = text_file.file  # type: ignore

    with contextlib.suppress(ModuleNotFoundError):
        from sanic.request import File as SanicUploadFile

        if isinstance(text_file, SanicUploadFile):
            return text_file.body.decode()

    return text_file.read().decode()


UploadScalar = GraphQLScalarType(
    name="Upload",
    description="The `Upload` scalar type represents a file upload.",
    serialize=lambda f: f,
    parse_value=lambda f: f,
    parse_literal=lambda node, vars=None: None,
)


def _parse_json_literal(node):
    if isinstance(node, ast.StringValue):
        return node.value
    if isinstance(node, ast.IntValue):
        return int(node.value)
    if isinstance(node, ast.FloatValue):
        return float(node.value)
    if isinstance(node, ast.BooleanValue):
        return node.value
    if isinstance(node, ast.NullValue):
        return None
    if isinstance(node, ast.ListValue):
        return [_parse_json_literal(v) for v in node.values]
    if isinstance(node, ast.ObjectValue):
        return {
            field.name.value: _parse_json_literal(field.value) for field in node.fields
        }
    return None


JSONScalar = GraphQLScalarType(
    name="JSON",
    description="Arbitrary JSON value",
    serialize=lambda v: v,
    parse_value=lambda v: v,
    parse_literal=_parse_json_literal,
)

FlavorEnum = GraphQLEnumType(
    name="Flavor",
    values={
        "VANILLA": GraphQLEnumValue("vanilla"),
        "STRAWBERRY": GraphQLEnumValue("strawberry"),
        "CHOCOLATE": GraphQLEnumValue("chocolate"),
    },
)

FolderInputType = GraphQLInputObjectType(
    name="FolderInput",
    fields={
        "files": GraphQLInputField(
            GraphQLNonNull(GraphQLList(GraphQLNonNull(UploadScalar)))
        ),
    },
)

DebugInfoType = GraphQLObjectType(
    name="DebugInfo",
    fields=lambda: {
        "numActiveResultHandlers": GraphQLField(GraphQLNonNull(GraphQLInt)),
        "isConnectionInitTimeoutTaskDone": GraphQLField(GraphQLBoolean),
    },
)


def resolve_greetings(_root, _info):
    return "hello"


def resolve_hello(_root, _info, name=None):
    return f"Hello {name or 'world'}"


async def resolve_async_hello(_root, _info, name=None, delay=0):
    await asyncio.sleep(delay)
    return f"Hello {name or 'world'}"


def resolve_always_fail(_root, _info):
    raise GraphQLError("You are not authorized")


def resolve_teapot(_root, info):
    info.context["response"].status_code = 418
    return "🫖"


def resolve_root_name(root, _info):
    return type(root).__name__


def resolve_value_from_context(_root, info):
    return info.context["custom_value"]


def resolve_value_from_extensions(_root, info, key):
    # raise NotImplementedError("Not implemented")
    return None
    # return info.input_extensions[key]


def resolve_returns401(_root, info):
    resp = info.context["response"]
    if hasattr(resp, "set_status"):
        resp.set_status(401)
    else:
        resp.status_code = 401
    return "hey"


def resolve_set_header(_root, info, name):
    info.context["response"].headers["X-Name"] = name
    return name


class Query:
    pass


QueryType = GraphQLObjectType(
    name="Query",
    fields={
        "greetings": GraphQLField(
            GraphQLNonNull(GraphQLString), resolve=resolve_greetings
        ),
        "hello": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={"name": GraphQLArgument(GraphQLString)},
            resolve=resolve_hello,
        ),
        "asyncHello": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={
                "name": GraphQLArgument(GraphQLString),
                "delay": GraphQLArgument(GraphQLFloat),
            },
            resolve=resolve_async_hello,
        ),
        "alwaysFail": GraphQLField(GraphQLString, resolve=resolve_always_fail),
        "teapot": GraphQLField(GraphQLNonNull(GraphQLString), resolve=resolve_teapot),
        "rootName": GraphQLField(
            GraphQLNonNull(GraphQLString), resolve=resolve_root_name
        ),
        "valueFromContext": GraphQLField(
            GraphQLNonNull(GraphQLString), resolve=resolve_value_from_context
        ),
        "valueFromExtensions": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={"key": GraphQLArgument(GraphQLNonNull(GraphQLString))},
            resolve=resolve_value_from_extensions,
        ),
        "returns401": GraphQLField(
            GraphQLNonNull(GraphQLString), resolve=resolve_returns401
        ),
        "setHeader": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={"name": GraphQLArgument(GraphQLNonNull(GraphQLString))},
            resolve=resolve_set_header,
        ),
    },
)


def resolve_echo(_root, _info, stringToEcho):
    return stringToEcho


def resolve_hello_mut(_root, _info):
    return "teststring"


def resolve_read_text(_root, _info, textFile):
    return _read_file(textFile)


def resolve_read_files(_root, _info, files):
    return [_read_file(f) for f in files]


def resolve_read_folder(_root, _info, folder):
    return [_read_file(f) for f in folder["files"]]


def resolve_match_text(_root, _info, textFile, pattern):
    text = textFile.read().decode()
    return pattern if pattern in text else ""


MutationType = GraphQLObjectType(
    name="Mutation",
    fields={
        "echo": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={"stringToEcho": GraphQLArgument(GraphQLNonNull(GraphQLString))},
            resolve=resolve_echo,
        ),
        "hello": GraphQLField(GraphQLNonNull(GraphQLString), resolve=resolve_hello_mut),
        "readText": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={"textFile": GraphQLArgument(GraphQLNonNull(UploadScalar))},
            resolve=resolve_read_text,
        ),
        "readFiles": GraphQLField(
            GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLString))),
            args={
                "files": GraphQLArgument(
                    GraphQLNonNull(GraphQLList(GraphQLNonNull(UploadScalar)))
                )
            },
            resolve=resolve_read_files,
        ),
        "readFolder": GraphQLField(
            GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLString))),
            args={"folder": GraphQLArgument(GraphQLNonNull(FolderInputType))},
            resolve=resolve_read_folder,
        ),
        "matchText": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={
                "textFile": GraphQLArgument(GraphQLNonNull(UploadScalar)),
                "pattern": GraphQLArgument(GraphQLNonNull(GraphQLString)),
            },
            resolve=resolve_match_text,
        ),
    },
)


async def subscribe_echo(root, info, message, delay=0):
    await asyncio.sleep(delay)
    yield message


async def subscribe_request_ping(_root, info):
    from graphql_server.subscriptions.protocols.graphql_transport_ws.types import (
        PingMessage,
    )

    ws = info.context["ws"]
    await ws.send_json(PingMessage({"type": "ping"}))
    yield True


async def subscribe_infinity(_root, info, message):
    Subscription.active_infinity_subscriptions += 1
    try:
        while True:
            yield message
            await asyncio.sleep(1)
    finally:
        Subscription.active_infinity_subscriptions -= 1


async def subscribe_context(_root, info):
    yield info.context["custom_value"]


async def subscribe_error_sub(_root, info, message):
    yield GraphQLError(message)


async def subscribe_exception(_root, _info, message):
    raise ValueError(message)
    yield


async def subscribe_flavors(_root, _info):
    yield "vanilla"
    yield "strawberry"
    yield "chocolate"


async def subscribe_flavors_invalid(_root, _info):
    yield "vanilla"
    yield "invalid type"
    yield "chocolate"


async def subscribe_debug(_root, info):
    active = [t for t in info.context["get_tasks"]() if not t.done()]
    timeout_task = info.context.get("connectionInitTimeoutTask")
    done = timeout_task.done() if timeout_task else None
    yield {
        "numActiveResultHandlers": len(active),
        "isConnectionInitTimeoutTaskDone": done,
    }


async def subscribe_listener(_root, info, timeout=None, group=None):
    yield info.context["request"].channel_name
    async with info.context["request"].listen_to_channel(
        type="test.message",
        timeout=timeout,
        groups=[group] if group is not None else [],
    ) as cm:
        async for msg in cm:
            yield msg["text"]


async def subscribe_listener_with_confirmation(_root, info, timeout=None, group=None):
    async with info.context["request"].listen_to_channel(
        type="test.message",
        timeout=timeout,
        groups=[group] if group is not None else [],
    ) as cm:
        yield None
        yield info.context["request"].channel_name
        async for msg in cm:
            yield msg["text"]


async def subscribe_connection_params(_root, info):
    yield info.context["connection_params"]


async def subscribe_long_finalizer(_root, _info, delay=0):
    try:
        for _ in range(100):
            yield "hello"
            await asyncio.sleep(0.01)
    finally:
        await asyncio.sleep(delay)


SubscriptionType = GraphQLObjectType(
    name="Subscription",
    fields={
        "echo": GraphQLField(
            GraphQLString,
            args={
                "message": GraphQLArgument(GraphQLNonNull(GraphQLString)),
                "delay": GraphQLArgument(GraphQLFloat),
            },
            subscribe=subscribe_echo,
            resolve=lambda payload, *args, **kwargs: payload,
        ),
        "requestPing": GraphQLField(
            GraphQLNonNull(GraphQLBoolean),
            subscribe=subscribe_request_ping,
            resolve=lambda payload, _info: payload,
        ),
        "infinity": GraphQLField(
            GraphQLString,
            args={"message": GraphQLArgument(GraphQLNonNull(GraphQLString))},
            subscribe=subscribe_infinity,
            resolve=lambda payload, *args, **kwargs: payload,
        ),
        "context": GraphQLField(
            GraphQLString,
            subscribe=subscribe_context,
            resolve=lambda payload, _info: payload,
        ),
        "error": GraphQLField(
            GraphQLString,
            args={"message": GraphQLArgument(GraphQLNonNull(GraphQLString))},
            subscribe=subscribe_error_sub,
            resolve=lambda payload, *args, **kwargs: payload,
        ),
        "exception": GraphQLField(
            GraphQLString,
            args={"message": GraphQLArgument(GraphQLNonNull(GraphQLString))},
            subscribe=subscribe_exception,
            resolve=lambda payload, *args, **kwargs: payload,
        ),
        "flavors": GraphQLField(
            FlavorEnum,
            subscribe=subscribe_flavors,
            resolve=lambda payload, _info: payload,
        ),
        "flavorsInvalid": GraphQLField(
            FlavorEnum,
            subscribe=subscribe_flavors_invalid,
            resolve=lambda payload, _info: payload,
        ),
        "debug": GraphQLField(
            DebugInfoType,
            subscribe=subscribe_debug,
            resolve=lambda payload, _info: payload,
        ),
        "listener": GraphQLField(
            GraphQLString,
            args={
                "timeout": GraphQLArgument(GraphQLFloat),
                "group": GraphQLArgument(GraphQLString),
            },
            subscribe=subscribe_listener,
            resolve=lambda payload, *args, **kwargs: payload,
        ),
        "listenerWithConfirmation": GraphQLField(
            GraphQLString,
            args={
                "timeout": GraphQLArgument(GraphQLFloat),
                "group": GraphQLArgument(GraphQLString),
            },
            subscribe=subscribe_listener_with_confirmation,
            resolve=lambda payload, *args, **kwargs: payload,
        ),
        "connectionParams": GraphQLField(
            JSONScalar,
            subscribe=subscribe_connection_params,
            resolve=lambda payload, _info: payload,
        ),
        "longFinalizer": GraphQLField(
            GraphQLString,
            args={"delay": GraphQLArgument(GraphQLFloat)},
            subscribe=subscribe_long_finalizer,
            resolve=lambda payload, *args, **kwargs: payload,
        ),
    },
)


class Subscription:
    active_infinity_subscriptions: int = 0


schema = GraphQLSchema(
    query=QueryType,
    mutation=MutationType,
    subscription=SubscriptionType,
)
