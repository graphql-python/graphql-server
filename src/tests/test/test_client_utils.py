import json
import types

import pytest

from graphql_server.test.client import BaseGraphQLTestClient


class DummyClient(BaseGraphQLTestClient):
    def request(self, body, headers=None, files=None):
        return types.SimpleNamespace(content=json.dumps(body).encode(), json=lambda: body)


def test_build_body_with_variables_and_files():
    client = DummyClient(None)
    variables = {"files": [None, None], "textFile": None, "other": "x"}
    files = {"file1": object(), "file2": object(), "textFile": object()}
    body = client._build_body("query", variables, files)
    mapping = json.loads(body["map"])
    assert mapping == {
        "file1": ["variables.files.0"],
        "file2": ["variables.files.1"],
        "textFile": ["variables.textFile"],
    }


def test_decode_multipart():
    client = DummyClient(None)
    response = types.SimpleNamespace(content=json.dumps({"a": 1}).encode())
    assert client._decode(response, type="multipart") == {"a": 1}


def test_query_deprecated_arg_and_assertion():
    client = DummyClient(None)
    with pytest.deprecated_call():
        resp = client.query("{a}", asserts_errors=False)
    assert resp.errors is None
