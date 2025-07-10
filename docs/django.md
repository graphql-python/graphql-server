# Django-GraphQL

Adds GraphQL support to your Django project.

## Installation

Install the integration with:

`pip install graphql-server[django]`

## Usage

Use the `GraphQLView` from `graphql_server.django`.

```python
from django.urls import path
from graphql_server.django import GraphQLView

from schema import schema

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema, graphiql=True)),
]
```

> **CORS**
>
> Enable CORS with [`django-cors-headers`](https://github.com/adamchainz/django-cors-headers).

### Supported options for GraphQLView

* `schema`
* `graphiql`
* `graphql_ide`
* `allow_queries_via_get`
* `multipart_uploads_enabled`


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user
```


## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
