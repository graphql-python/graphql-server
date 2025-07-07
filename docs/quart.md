# Quart-GraphQL

Adds GraphQL support to your Quart application.

## Installation

Install with:

`pip install graphql-server[quart]`

## Usage

Use the `GraphQLView` from `graphql_server.quart`.

```python
from quart import Quart
from graphql_server.quart import GraphQLView

from schema import schema

app = Quart(__name__)

app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view(schema=schema, graphiql=True),
)
```

> **CORS**
>
> Use [quart_cors](https://github.com/corydolphin/quart-cors) to enable CORS:
> ```python
> from quart_cors import cors
>
> app = cors(app, allow_origin="*")
> ```

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


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user
```


## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
