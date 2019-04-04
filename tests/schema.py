from graphql.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, GraphQLObjectType
from graphql.type.scalars import GraphQLString
from graphql.type.schema import GraphQLSchema


def resolve_raises(*_):
    raise Exception("Throws!")


QueryRootType = GraphQLObjectType(
    name='QueryRoot',
    fields={
        'thrower': GraphQLField(GraphQLNonNull(GraphQLString),
                                resolve=resolve_raises),
        'request': GraphQLField(GraphQLNonNull(GraphQLString)),
        'context': GraphQLField(GraphQLNonNull(GraphQLString)),
        'test': GraphQLField(
            type_=GraphQLString,
            args={
                'who': GraphQLArgument(GraphQLString)
            },
            resolve=lambda obj, info, who='World': 'Hello %s' % who
        )
    }
)

MutationRootType = GraphQLObjectType(
    name='MutationRoot',
    fields={
        'writeTest': GraphQLField(
            type_=QueryRootType,
            resolve=lambda *_: QueryRootType
        )
    }
)

schema = GraphQLSchema(QueryRootType, MutationRootType)
