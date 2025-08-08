import pytest
from graphql import (
    ExecutionResult,
    GraphQLField,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    GraphQLError,
    parse,
)

import graphql_server.runtime as runtime


schema = GraphQLSchema(
    query=GraphQLObjectType('Query', {'hello': GraphQLField(GraphQLString)})
)


def test_validate_document_with_rules():
    from graphql.validation.rules.no_unused_fragments import NoUnusedFragmentsRule

    doc = parse('query Test { hello }')
    assert runtime.validate_document(schema, doc, (NoUnusedFragmentsRule,)) == []


def test_get_custom_context_kwargs(monkeypatch):
    assert runtime._get_custom_context_kwargs({'a': 1}) == {'operation_extensions': {'a': 1}}
    monkeypatch.setattr(runtime, 'IS_GQL_33', False)
    try:
        assert runtime._get_custom_context_kwargs({'a': 1}) == {}
    finally:
        monkeypatch.setattr(runtime, 'IS_GQL_33', True)


def test_get_operation_type_multiple_operations():
    doc = parse('query A{hello} query B{hello}')
    with pytest.raises(Exception):
        runtime._get_operation_type(doc)


def test_parse_and_validate_document_node():
    doc = parse('query Q { hello }')
    res = runtime._parse_and_validate(schema, doc, None)
    assert res == doc


def test_introspect_success_and_failure(monkeypatch):
    data = runtime.introspect(schema)
    assert '__schema' in data

    def fake_execute_sync(schema, query):
        return ExecutionResult(data=None, errors=[GraphQLError('boom')])

    monkeypatch.setattr(runtime, 'execute_sync', fake_execute_sync)
    with pytest.raises(ValueError):
        runtime.introspect(schema)
