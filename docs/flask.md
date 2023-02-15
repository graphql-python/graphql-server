# Flask-GraphQL

Adds GraphQL support to your Flask application.

## Installation

To install the integration with Flask, run the below command on your terminal.

`pip install graphql-server[flask]`

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

This will add `/graphql` endpoint to your app and enable the GraphiQL IDE.

### Supported options for GraphQLView

 * `schema`: The GraphQL schema object that you want the view to execute when it gets a valid request. Accepts either an object of type `GraphQLSchema` from `graphql-core` or `Schema` from `graphene`. For Graphene v3, passing either `schema: graphene.Schema` or `schema.graphql_schema` is allowed.
 * `context`: A value to pass as the `context_value` to graphql `execute` function. By default is set to `dict` with request object at key `request`.
 * `root_value`: The `root_value` you want to provide to graphql `execute`.
 * `pretty`: Whether or not you want the response to be pretty printed JSON.
 * `graphiql`: If `True`, may present [GraphiQL](https://github.com/graphql/graphiql) when loaded directly from a browser (a useful tool for debugging and exploration).
 * `graphiql_version`: The graphiql version to load. Defaults to **"2.2.0"**.
 * `graphiql_template`: Inject a Jinja template string to customize GraphiQL.
 * `graphiql_html_title`: The graphiql title to display. Defaults to **"GraphiQL"**.
 * `jinja_env`: Sets jinja environment to be used to process GraphiQL template. If environment is not set, fallbacks to simple regex-based renderer.
 * `batch`: Set the GraphQL view as batch (for using in [Apollo-Client](http://dev.apollodata.com/core/network.html#query-batching) or [ReactRelayNetworkLayer](https://github.com/nodkz/react-relay-network-layer))
 * `middleware`: A list of graphql [middlewares](http://docs.graphene-python.org/en/latest/execution/middleware/).
 * `validation_rules`: A list of graphql validation rules.
 * `execution_context_class`: Specifies a custom execution context class.
 * `encode`: the encoder to use for responses (sensibly defaults to `graphql_server.json_encode`).
 * `format_error`: the error formatter to use for responses (sensibly defaults to `graphql_server.default_format_error`.
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
See [CONTRIBUTING.md](../CONTRIBUTING.md)
