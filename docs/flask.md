# Flask-GraphQL

Adds GraphQL support to your Flask application.

## Installation

To install the integration with Flask, run the below command on your terminal.

`pip install graphql-server-core[flask]`

## Usage

Use the `GraphQLView` view from `graphql_server.flask`.

```python
from flask import Flask
from graphql_server.flask import GraphQLView

from schema import schema

app = Flask(__name__)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
    'graphql',
    schema=schema,
    graphiql=True,
))

# Optional, for adding batch query support (used in Apollo-Client)
app.add_url_rule('/graphql/batch', view_func=GraphQLView.as_view(
    'graphql',
    schema=schema,
    batch=True
))

if __name__ == '__main__':
    app.run()
```

This will add `/graphql` and `/graphiql` endpoints to your app.

### Special Note for GraphQL-Server V3

If you are using the `Schema` type of [Graphene](https://github.com/graphql-python/graphene) library, be sure to use the `graphql_schema` attribute to pass as schema on the `GraphQLView` view. Otherwise, the `GraphQLSchema` from `graphql-core` is the way to go.

**Graphene Schema**

```python
from graphene import ObjectType, String, Schema


class Query(ObjectType):
    # this defines a Field `hello` in our Schema with a single Argument `name`
    hello = String(name=String(default_value="stranger"))
    goodbye = String()

    # our Resolver method takes the GraphQL context (root, info) as well as
    # Argument (name) for the Field and returns data for the query Response
    @staticmethod
    def resolve_hello(root, info, name):
        return f'Hello {name}!'

    @staticmethod
    def resolve_goodbye(root, info):
        return 'See ya!'

# Use the `graphql_schema` if using `Schema` type
schema = Schema(query=Query).graphql_schema
```

**Graphql-Core Schema**

```python
from graphql import GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString


schema = GraphQLSchema(
    query=GraphQLObjectType(
        name='RootQueryType',
        fields={
            'hello': GraphQLField(
                GraphQLString,
                resolve=lambda obj, info: 'world')
        }))
```


### Supported options

 * `schema`: The `GraphQLSchema` object that you want the view to execute when it gets a valid request.
 * `context`: A value to pass as the `context_value` to graphql `execute` function.
 * `root_value`: The `root_value` you want to provide to graphql `execute`.
 * `pretty`: Whether or not you want the response to be pretty printed JSON.
 * `graphiql`: If `True`, may present [GraphiQL](https://github.com/graphql/graphiql) when loaded directly from a browser (a useful tool for debugging and exploration).
 * `graphiql_version`: The graphiql version to load. Defaults to **"1.0.3"**.
 * `graphiql_template`: Inject a Jinja template string to customize GraphiQL.
 * `graphiql_html_title`: The graphiql title to display. Defaults to **"GraphiQL"**.
 * `batch`: Set the GraphQL view as batch (for using in [Apollo-Client](http://dev.apollodata.com/core/network.html#query-batching) or [ReactRelayNetworkLayer](https://github.com/nodkz/react-relay-network-layer))
 * `middleware`: A list of graphql [middlewares](http://docs.graphene-python.org/en/latest/execution/middleware/).
 * `subscriptions`: The GraphiQL socket endpoint for using subscriptions in graphql-ws.
 * `headers`: An optional GraphQL string to use as the initial displayed request headers, if not provided, the stored headers will be used.
 * `default_query`: An optional GraphQL string to use when no query is provided and no stored query exists from a previous session. If not provided, GraphiQL will use its own default query.
* `header_editor_enabled`: An optional boolean which enables the header editor when true. Defaults to **false**.
* `should_persist_headers`:  An optional boolean which enables to persist headers to storage when true. Defaults to **false**.


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value
per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user

```

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)