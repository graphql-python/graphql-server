from graphql import (
    GraphQLField,
    GraphQLID,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
)

import tests.c


def fields():
    from tests.c import CType

    async def resolve_c_list(root, info):
        return [tests.c.C(id=root.id)]

    return {
        "id": GraphQLField(GraphQLNonNull(GraphQLID)),
        "cList": GraphQLField(
            # non-null list of non-null C
            GraphQLNonNull(GraphQLList(GraphQLNonNull(CType))),
            resolve=resolve_c_list,
        ),
    }


DType = GraphQLObjectType(
    name="D",
    fields=fields,
)
