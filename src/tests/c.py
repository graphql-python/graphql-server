from graphql import GraphQLField, GraphQLID, GraphQLNonNull, GraphQLObjectType


class C:
    def __init__(self, id: str):
        self.id = id


CType = GraphQLObjectType(
    name="C",
    fields={"id": GraphQLField(GraphQLNonNull(GraphQLID))},
)
