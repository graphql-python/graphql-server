# ASGI-GraphQL

Adds GraphQL support to any ASGI framework.

## Installation

Install the ASGI integration with:

`pip install graphql-server[asgi]`

## Usage

Use the `GraphQL` class from `graphql_server.asgi`.

```python
from starlette.applications import Starlette
from graphql_server.asgi import GraphQL

from schema import schema

app = Starlette()

graphql_app = GraphQL(schema=schema, graphiql=True)
app.mount("/graphql", graphql_app)
```

> **CORS**
>
> Add Starlette's `CORSMiddleware` if you need cross-origin requests:
> ```python
> from starlette.middleware.cors import CORSMiddleware
> app.add_middleware(
>     CORSMiddleware,
>     allow_origins=["*"],
>     allow_methods=["*"],
>     allow_headers=["*"],
> )
> ```

This mounts `/graphql` in your ASGI app and enables the GraphiQL IDE.

### Supported options for GraphQL

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


You can also subclass `GraphQL` and overwrite `get_root_value(self, request)` to have a dynamic root value
per request.

```python
class UserRootValue(GraphQL):
    def get_root_value(self, request):
        return request.user

```


## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
