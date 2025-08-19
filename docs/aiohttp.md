# aiohttp-Graphql

Adds GraphQL support to your aiohttp application.

## Installation

To install the integration with aiohttp, run the following command in your terminal.

`pip install graphql-server[aiohttp]`

## Usage

Use the `GraphQLView` view from `graphql_server.aiohttp`

```python
from aiohttp import web
from graphql_server.aiohttp import GraphQLView

from schema import schema

app = web.Application()

GraphQLView.attach(app, schema=schema, graphiql=True)

# Optional, for adding batch query support (used in Apollo-Client)
GraphQLView.attach(app, schema=schema, batch=True, route_path="/graphql/batch")

if __name__ == '__main__':
    web.run_app(app)
```

This will add `/graphql` endpoint to your app (customizable by passing `route_path='/mypath'` to `GraphQLView.attach`) and enable the GraphiQL IDE.
> **CORS**
> 
> Use [aiohttp_cors](https://github.com/aio-libs/aiohttp-cors) to allow cross origin requests:
> ```python
> import aiohttp_cors
> 
> cors = aiohttp_cors.setup(app)
> for route in list(app.router.routes()):
>     cors.add(route)
> ```


Note: `GraphQLView.attach` is just a convenience function, and the same functionality can be achieved with

```python
gql_view = GraphQLView(schema=schema, graphiql=True)
app.router.add_route('*', '/graphql', gql_view, name='graphql')
```

It's worth noting that the the "view function" of `GraphQLView` is contained in `GraphQLView.__call__`. So, when you create an instance, that instance is callable with the request object as the sole positional argument. To illustrate:

```python
gql_view = GraphQLView(schema=Schema, **kwargs)
gql_view(request)  # <-- the instance is callable and expects a `aiohttp.web.Request` object.
```

### Supported options for GraphQLView

* `schema`
* `graphiql`
* `graphql_ide`
* `allow_queries_via_get`
* `keep_alive`
* `keep_alive_interval`
* `debug`
* `subscription_protocols`
* `connection_init_wait_timeout`
* `multipart_uploads_enabled`

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
