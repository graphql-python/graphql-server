from graphql.type.definition import (
    GraphQLArgument,
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
)
from graphql.type.scalars import GraphQLString
from graphql.type.schema import GraphQLSchema


def resolve_error(*_args):
    raise ValueError("Throws!")


def resolve_request(_obj, info):
    return info.context.get("q")


def resolve_context(_obj, info):
    return str(info.context)


def resolve_test(_obj, _info, who="World"):
    return "Hello {}".format(who)


NonNullString = GraphQLNonNull(GraphQLString)

QueryRootType = GraphQLObjectType(
    name="QueryRoot",
    fields={
        "error": GraphQLField(NonNullString, resolver=resolve_error),
        "request": GraphQLField(NonNullString, resolver=resolve_request),
        "context": GraphQLField(NonNullString, resolver=resolve_context),
        "test": GraphQLField(
            GraphQLString,
            {"who": GraphQLArgument(GraphQLString)},
            resolver=resolve_test,
        ),
    },
)

MutationRootType = GraphQLObjectType(
    name="MutationRoot",
    fields={
        "writeTest": GraphQLField(
            type=QueryRootType, resolver=lambda *_args: QueryRootType
        )
    },
)

schema = GraphQLSchema(QueryRootType, MutationRootType)
