import builtins

import pytest

from graphql_server.utils.debug import GraphQLJSONEncoder, pretty_print_graphql_operation


def test_graphql_json_encoder_default():
    class Foo:
        pass

    foo = Foo()
    encoder = GraphQLJSONEncoder()
    assert encoder.default(foo) == repr(foo)


def test_pretty_print_requires_pygments(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("pygments"):
            raise ImportError("No module named pygments")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError):
        pretty_print_graphql_operation("Query", "query { field }", None)


def test_pretty_print_graphql_operation(capsys):
    obj = object()
    variables = {"var": obj}
    pretty_print_graphql_operation("MyQuery", "query { field }", variables)
    captured = capsys.readouterr().out
    assert "MyQuery" in captured
    assert "field" in captured
    assert "var" in captured
    assert repr(obj) in captured


def test_pretty_print_introspection_query(capsys):
    pretty_print_graphql_operation(
        "IntrospectionQuery", "query { __schema { queryType { name } } }", None
    )
    captured = capsys.readouterr().out
    assert captured == ""
