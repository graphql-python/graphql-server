# Channels-GraphQL

Adds GraphQL over HTTP and WebSockets to Django Channels.

## Installation

Install with:

`pip install graphql-server[channels]`

## Usage

Use `GraphQLProtocolTypeRouter` from `graphql_server.channels`.

```python
from channels.routing import ProtocolTypeRouter
from graphql_server.channels import GraphQLProtocolTypeRouter

from schema import schema

application = ProtocolTypeRouter(
    {
        "": GraphQLProtocolTypeRouter(schema, url_pattern=r"^graphql"),
    }
)
```

> **CORS**
>
> Use [`django-cors-headers`](https://github.com/adamchainz/django-cors-headers) for cross-origin requests.

### Supported options for GraphQLProtocolTypeRouter

* `schema`
* `django_application`
* `url_pattern`
* `http_consumer_class`
* `ws_consumer_class`


You can also subclass `GraphQLView` and overwrite `get_root_value(self, request)` to have a dynamic root value per request.

```python
class UserRootValue(GraphQLView):
    def get_root_value(self, request):
        return request.user
```


## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md)
