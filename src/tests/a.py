from graphql import (
    GraphQLField,
    GraphQLID,
    GraphQLNonNull,
    GraphQLObjectType,
)


class A:
    def __init__(self, id: str):
        self.id = id


def fields():
    import tests.b
    from tests.b import BType

    async def resolve_b(root, info):
        # mirrors: return B(id=self.id)
        return tests.b.B(id=root.id)

    async def resolve_optional_b(root, info):
        return tests.b.B(id=root.id)

    async def resolve_optional_b2(root, info):
        return tests.b.B(id=root.id)

    return {
        "id": GraphQLField(GraphQLNonNull(GraphQLID)),
        "b": GraphQLField(
            GraphQLNonNull(BType),
            resolve=resolve_b,
        ),
        "optionalB": GraphQLField(
            BType,
            resolve=resolve_optional_b,
        ),
        "optionalB2": GraphQLField(
            BType,
            resolve=resolve_optional_b2,
        ),
    }


AType = GraphQLObjectType(
    name="A",
    # use a thunk so that BType is available even though it’s defined above
    fields=fields,
)
