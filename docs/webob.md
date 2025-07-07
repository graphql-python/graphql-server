# WebOb-GraphQL

Adds GraphQL support to your WebOb (Pyramid, Pylons, ...) application.

## Installation

To install the integration with WebOb, run the below command on your terminal.

`pip install graphql-server[webob]`

## Usage

Use the `GraphQLView` view from `graphql_server.webob`

### Pyramid

```python
from wsgiref.simple_server import make_server
from pyramid.config import Configurator

from graphql_server.webob import GraphQLView

from schema import schema

def graphql_view(request):
    return GraphQLView(request=request, schema=schema, graphiql=True).dispatch_request(request)

if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('graphql', '/graphql')
        config.add_view(graphql_view, route_name='graphql')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
```

This will add `/graphql` endpoint to your app and enable the GraphiQL IDE.
### Enabling CORS
> **CORS**
>
> Include [pyramid-cors](https://github.com/Kinto/pyramid-cors) in your Pyramid configuration:
> ```python
> config.include("pyramid_cors")
> ```


### Supported options for GraphQLView
* `schema`
* `graphiql`
* `graphql_ide`
* `multipart_uploads_enabled`
* `allow_queries_via_get`

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
