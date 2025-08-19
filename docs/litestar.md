# Litestar-GraphQL

Adds GraphQL support to your Litestar application.

## Installation

Install with:

`pip install graphql-server[litestar]`

## Usage

Use `make_graphql_controller` from `graphql_server.litestar`.

```python
from litestar import Litestar
from graphql_server.litestar import make_graphql_controller

from schema import schema

GraphQLController = make_graphql_controller(schema, path="/graphql")

app = Litestar(route_handlers=[GraphQLController])
```

> **CORS**
>
> To enable CORS you can pass a `CORSConfig` to `Litestar`:
> ```python
> from litestar.config.cors import CORSConfig
>
> cors_config = CORSConfig(allow_origins=["*"])
> app = Litestar(route_handlers=[GraphQLController], cors_config=cors_config)
> ```

### Supported options for GraphQLController

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

You can also subclass `GraphQLController` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLController):
    def get_root_value(self, request):
        return request.user
```


## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
