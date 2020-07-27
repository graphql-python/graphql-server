# Sanic-GraphQL

Adds GraphQL support to your Sanic application.

## Installation

To install the integration with Sanic, run the below command on your terminal.

`pip install graphql-server[sanic]`

## Usage

Use the `GraphQLView` view from `graphql_server.sanic`

```python
from graphql_server.sanic import GraphQLView
from sanic import Sanic

from schema import schema

app = Sanic(name="Sanic Graphql App")

app.add_route(
    GraphQLView.as_view(schema=schema, graphiql=True),
    '/graphql'
)

# Optional, for adding batch query support (used in Apollo-Client)
app.add_route(
    GraphQLView.as_view(schema=schema, batch=True),
    '/graphql/batch'
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

This will add `/graphql` endpoint to your app and enable the GraphiQL IDE.

### Supported options for GraphQLView

 * `schema`: The `GraphQLSchema` object that you want the view to execute when it gets a valid request.
 * `context`: A value to pass as the `context_value` to graphql `execute` function. By default is set to `dict` with request object at key `request`.
 * `root_value`: The `root_value` you want to provide to graphql `execute`.
 * `pretty`: Whether or not you want the response to be pretty printed JSON.
 * `graphiql`: If `True`, may present [GraphiQL](https://github.com/graphql/graphiql) when loaded directly from a browser (a useful tool for debugging and exploration).
 * `graphiql_version`: The graphiql version to load. Defaults to **"1.0.3"**.
 * `graphiql_template`: Inject a Jinja template string to customize GraphiQL.
 * `graphiql_html_title`: The graphiql title to display. Defaults to **"GraphiQL"**.
 * `jinja_env`: Sets jinja environment to be used to process GraphiQL template. If Jinja’s async mode is enabled (by `enable_async=True`), uses 
`Template.render_async` instead of `Template.render`. If environment is not set, fallbacks to simple regex-based renderer.
 * `batch`: Set the GraphQL view as batch (for using in [Apollo-Client](http://dev.apollodata.com/core/network.html#query-batching) or [ReactRelayNetworkLayer](https://github.com/nodkz/react-relay-network-layer))
 * `middleware`: A list of graphql [middlewares](http://docs.graphene-python.org/en/latest/execution/middleware/).
 * `max_age`: Sets the response header Access-Control-Max-Age for preflight requests.
 * `encode`: the encoder to use for responses (sensibly defaults to `graphql_server.json_encode`).
 * `format_error`: the error formatter to use for responses (sensibly defaults to `graphql_server.default_format_error`.
 * `enable_async`: whether `async` mode will be enabled.
 * `subscriptions`: The GraphiQL socket endpoint for using subscriptions in graphql-ws.
 * `headers`: An optional GraphQL string to use as the initial displayed request headers, if not provided, the stored headers will be used.
 * `default_query`: An optional GraphQL string to use when no query is provided and no stored query exists from a previous session. If not provided, GraphiQL will use its own default query.
* `header_editor_enabled`: An optional boolean which enables the header editor when true. Defaults to **false**.
* `should_persist_headers`:  An optional boolean which enables to persist headers to storage when true. Defaults to **false**.


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user
```

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)