<img src="https://raw.githubusercontent.com/graphql-python/graphql-server/master/docs/_static/graphql-server-logo.svg" height="128px">

[![PyPI version](https://badge.fury.io/py/graphql-server.svg)](https://badge.fury.io/py/graphql-server)
[![Coverage Status](https://codecov.io/gh/graphql-python/graphql-server/branch/master/graph/badge.svg)](https://codecov.io/gh/graphql-python/graphql-server)

GraphQL-Server is a base library that serves as a helper
for building GraphQL servers or integrations into existing web frameworks using
[GraphQL-Core](https://github.com/graphql-python/graphql-core).
* ✅ It passes all the GraphQL spec tests
* Supports 💾 `Upload`s, 🔁 Sync, 🔀 Async views and 🔄 Subscriptions through WebSockets.
* 🚀 It integrates seamlessly with all HTTP/Websocket Python servers

## Integrations built with GraphQL-Server

| Server integration          | Docs                                                                                    |
| --------------------------- | --------------------------------------------------------------------------------------- |
| aiohttp                     | [aiohttp](https://github.com/graphql-python/graphql-server/blob/master/docs/aiohttp.md) |
| asgi                       | [asgi](https://github.com/graphql-python/graphql-server/blob/master/docs/asgi.md)     |
| Chalice                       | [chalice](https://github.com/graphql-python/graphql-server/blob/master/docs/chalice.md)     |
| Channels (Django)           | [channels](https://github.com/graphql-python/graphql-server/blob/master/docs/channels.md)     |
| Django                       | [django](https://github.com/graphql-python/graphql-server/blob/master/docs/django.md)     |
| FastAPI                       | [fastapi](https://github.com/graphql-python/graphql-server/blob/master/docs/fastapi.md)     |
| Flask                       | [flask](https://github.com/graphql-python/graphql-server/blob/master/docs/flask.md)     |
| Litestar                       | [litestar](https://github.com/graphql-python/graphql-server/blob/master/docs/litestar.md)     |
| Quart                       | [quart](https://github.com/graphql-python/graphql-server/blob/master/docs/quart.md)     |
| Sanic                       | [sanic](https://github.com/graphql-python/graphql-server/blob/master/docs/sanic.md)     |
| WebOb                       | [webob](https://github.com/graphql-python/graphql-server/blob/master/docs/webob.md)     |

## Documentation

The `graphql_server` package provides these public helper functions:

- `execute`
- `execute_sync`
- `subscribe`

All functions in the package are annotated with type hints and docstrings,
and you can build HTML documentation from these using `bin/build_docs`.

You can also use one of the existing integrations listed above as
blueprint to build your own integration or GraphQL server implementations.

Please let us know when you have built something new, so we can list it here.

## Contributing

See [CONTRIBUTING.md](https://github.com/graphql-python/graphql-server/blob/master/CONTRIBUTING.md)

## Licensing

The code in this project is licensed under MIT license. See [LICENSE](./LICENSE)
for more information.

![Recent Activity](https://images.repography.com/0/graphql-python/graphql-server/recent-activity/d751713988987e9331980363e24189ce.svg)
