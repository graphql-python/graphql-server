from types import SimpleNamespace

from graphql_server.django.context import GraphQLDjangoContext


def test_graphql_django_context_get_and_item_access():
    req = SimpleNamespace()
    res = SimpleNamespace()
    ctx = GraphQLDjangoContext(req, res)
    assert ctx["request"] is req
    assert ctx.get("response") is res
