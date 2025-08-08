import json

from graphql_server.http.base import BaseView


class DummyView(BaseView):
    graphql_ide = None


def test_parse_query_params_extensions():
    view = DummyView()
    params = view.parse_query_params({"extensions": json.dumps({"a": 1})})
    assert params["extensions"] == {"a": 1}


def test_is_multipart_subscriptions_boundary_check():
    view = DummyView()
    assert not view._is_multipart_subscriptions(
        "multipart/mixed", {"boundary": "notgraphql"}
    )
