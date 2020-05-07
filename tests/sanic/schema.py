import asyncio

from graphql.type.definition import (
    GraphQLArgument,
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
)
from graphql.type.scalars import GraphQLString
from graphql.type.schema import GraphQLSchema


def resolve_raises(*_):
    raise Exception("Throws!")


# Sync schema
QueryRootType = GraphQLObjectType(
    name="QueryRoot",
    fields={
        "thrower": GraphQLField(GraphQLNonNull(GraphQLString), resolve=resolve_raises),
        "request": GraphQLField(
            GraphQLNonNull(GraphQLString),
            resolve=lambda obj, info: info.context["request"].args.get("q"),
        ),
        "context": GraphQLField(
            GraphQLNonNull(GraphQLString), resolve=lambda obj, info: info.context
        ),
        "test": GraphQLField(
            type_=GraphQLString,
            args={"who": GraphQLArgument(GraphQLString)},
            resolve=lambda obj, info, who=None: "Hello %s" % (who or "World"),
        ),
    },
)

MutationRootType = GraphQLObjectType(
    name="MutationRoot",
    fields={
        "writeTest": GraphQLField(type_=QueryRootType, resolve=lambda *_: QueryRootType)
    },
)

Schema = GraphQLSchema(QueryRootType, MutationRootType)


# Schema with async methods
async def resolver(context, *_, **__):
    await asyncio.sleep(0.001)
    return "hey"


async def resolver_2(context, *_, **__):
    await asyncio.sleep(0.003)
    return "hey2"


def resolver_3(context, *_, **__):
    return "hey3"


AsyncQueryType = GraphQLObjectType(
    "AsyncQueryType",
    {
        "a": GraphQLField(GraphQLString, resolve=resolver),
        "b": GraphQLField(GraphQLString, resolve=resolver_2),
        "c": GraphQLField(GraphQLString, resolve=resolver_3),
    },
)

AsyncSchema = GraphQLSchema(AsyncQueryType)
