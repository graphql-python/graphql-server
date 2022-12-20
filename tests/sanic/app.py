from urllib.parse import urlencode

from sanic import Sanic

from graphql_server.sanic import GraphQLView

from .schema import Schema

Sanic.test_mode = True


def create_app(path="/graphql", **kwargs):
    app = Sanic("TestApp")

    schema = kwargs.pop("schema", None) or Schema
    app.add_route(GraphQLView.as_view(schema=schema, **kwargs), path)

    return app


def url_string(uri="/graphql", **url_params):
    string = "/graphql"

    if url_params:
        string += "?" + urlencode(url_params)

    return string
