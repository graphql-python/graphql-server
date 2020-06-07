from urllib.parse import urlencode

from webob import Request

from graphql_server.webob import GraphQLView
from tests.webob.schema import Schema


def url_string(**url_params):
    string = "/graphql"

    if url_params:
        string += "?" + urlencode(url_params)

    return string


class Client(object):
    def __init__(self, **kwargs):
        self.schema = kwargs.pop("schema", None) or Schema
        self.settings = kwargs.pop("settings", None) or {}

    def get(self, url, **extra):
        request = Request.blank(url, method="GET", **extra)
        context_value = self.settings.pop("context_value", request)
        response = GraphQLView(
            request=request,
            schema=self.schema,
            context_value=context_value,
            **self.settings
        )
        return response.dispatch_request()

    def post(self, url, **extra):
        extra["POST"] = extra.pop("data")
        request = Request.blank(url, method="POST", **extra)
        context_value = self.settings.pop("context_value", request)
        response = GraphQLView(
            request=request,
            schema=self.schema,
            context_value=context_value,
            **self.settings
        )
        return response.dispatch_request()

    def put(self, url, **extra):
        request = Request.blank(url, method="PUT", **extra)
        context_value = self.settings.pop("context_value", request)
        response = GraphQLView(
            request=request,
            schema=self.schema,
            context_value=context_value,
            **self.settings
        )
        return response.dispatch_request()
