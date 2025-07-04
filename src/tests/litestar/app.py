from typing import Any

from graphql_server.litestar import make_graphql_controller
from litestar import Litestar, Request
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from tests.views.schema import schema


def custom_context_dependency() -> str:
    return "Hi!"


async def get_root_value(request: Request = None):
    return request


async def get_context(app_dependency: str, request: Request = None):
    return {"custom_value": app_dependency, "request": request}


def create_app(schema=schema, **kwargs: Any):
    GraphQLController = make_graphql_controller(
        schema,
        path="/graphql",
        context_getter=get_context,
        root_value_getter=get_root_value,
        **kwargs,
    )

    cors_config = CORSConfig(allow_origins=["*"])

    return Litestar(
        route_handlers=[GraphQLController],
        dependencies={
            "app_dependency": Provide(custom_context_dependency, sync_to_thread=True)
        },
        cors_config=cors_config,
    )
