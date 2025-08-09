# FastAPI-GraphQL

Adds GraphQL support to your FastAPI application.

## Installation

Install with:

`pip install graphql-server[fastapi]`

## Usage

Use the `GraphQLRouter` from `graphql_server.fastapi`.

```python
from fastapi import FastAPI
from graphql_server.fastapi import GraphQLRouter

from schema import schema

app = FastAPI()

graphql_app = GraphQLRouter(schema=schema, graphiql=True)
app.include_router(graphql_app, prefix="/graphql")
```

> **CORS**
>
> Use FastAPI's `CORSMiddleware` to enable cross-origin requests:
> ```python
> from fastapi.middleware.cors import CORSMiddleware
>
> app.add_middleware(
>     CORSMiddleware,
>     allow_origins=["*"],
>     allow_methods=["*"],
>     allow_headers=["*"],
> )
> ```

### Supported options for GraphQLRouter

* `schema`
* `path`
* `graphiql`
* `graphql_ide`
* `allow_queries_via_get`
* `keep_alive`
* `keep_alive_interval`
* `debug`
* `root_value_getter`
* `context_getter`
* `subscription_protocols`
* `connection_init_wait_timeout`
* `multipart_uploads_enabled`


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value
per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user

```

You can also subclass `GraphQLRouter` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLRouter):
    def get_root_value(self, request):
        return request.user
```

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
