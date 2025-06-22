from graphql import (
    GraphQLField,
    GraphQLID,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
)


class B:
    def __init__(self, id: str):
        self.id = id


def fields():
    import tests.a
    from tests.a import AType

    async def resolve_a(root, info):
        return tests.a.A(id=root.id)

    async def resolve_a_list(root, info):
        return [tests.a.A(id=root.id)]

    async def resolve_optional_a(root, info):
        return tests.a.A(id=root.id)

    async def resolve_optional_a2(root, info):
        return tests.a.A(id=root.id)

    return {
        "id": GraphQLField(GraphQLNonNull(GraphQLID)),
        "a": GraphQLField(
            GraphQLNonNull(AType),
            resolve=resolve_a,
        ),
        "aList": GraphQLField(
            GraphQLNonNull(GraphQLList(GraphQLNonNull(AType))),
            resolve=resolve_a_list,
        ),
        "optionalA": GraphQLField(
            AType,
            resolve=resolve_optional_a,
        ),
        "optionalA2": GraphQLField(
            AType,
            resolve=resolve_optional_a2,
        ),
    }


BType = GraphQLObjectType(
    name="B",
    fields=fields,
)
