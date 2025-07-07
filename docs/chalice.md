# Chalice-GraphQL

Adds GraphQL support to your AWS Chalice application.

## Installation

Install the Chalice integration with:

`pip install graphql-server[chalice]`

## Usage

Use the `GraphQLView` from `graphql_server.chalice`.

```python
from chalice import Chalice
from graphql_server.chalice import GraphQLView

from schema import schema

app = Chalice(app_name="MyApp")

@app.route("/graphql", methods=["GET", "POST"])
def graphql_server():
    view = GraphQLView(schema=schema, graphiql=True)
    return view.execute_request(app.current_request)
```

> **CORS**
>
> To allow CORS, create a `CORSConfig` and pass it when defining the route:
> ```python
> from chalice import CORSConfig
>
> cors_config = CORSConfig(allow_origin="*")
> @app.route("/graphql", methods=["GET", "POST"], cors=cors_config)
> def graphql_server():
>     view = GraphQLView(schema=schema, graphiql=True)
>     return view.execute_request(app.current_request)
> ```

This adds a `/graphql` route with GraphiQL enabled.

### Supported options for GraphQLView

* `schema`
* `graphiql`
* `graphql_ide`
* `allow_queries_via_get`


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user
```



## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
