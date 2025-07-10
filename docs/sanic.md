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
> **CORS**
>
> Install [sanic-cors](https://github.com/ashleysommer/sanic-cors) and initialize it with your app:
> ```python
> from sanic_cors import CORS
> CORS(app)
> ```

### Supported options for GraphQLView

* `schema`
* `graphiql`
* `graphql_ide`
* `allow_queries_via_get`
* `json_encoder`
* `json_dumps_params`
* `multipart_uploads_enabled`


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user
```

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
