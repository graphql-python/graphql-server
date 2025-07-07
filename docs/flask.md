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
> **CORS**
>
> Install [Flask-CORS](https://flask-cors.readthedocs.io/) and initialize it with your app:
> ```python
> from flask_cors import CORS
> CORS(app)
> ```

### Supported options for GraphQLView

* `schema`
* `graphiql`
* `graphql_ide`
* `allow_queries_via_get`
* `multipart_uploads_enabled`


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value
per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user

```

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
