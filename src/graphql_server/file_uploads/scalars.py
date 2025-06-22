from graphql.type import GraphQLScalarType

Upload = GraphQLScalarType("Upload", serialize=bytes, parse_value=lambda x: bytes(x))

__all__ = ["Upload"]
