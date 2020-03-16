from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.type.definition import GraphQLField, GraphQLNonNull, GraphQLObjectType
from graphql.type.scalars import GraphQLString
from graphql.type.schema import GraphQLSchema
from promise import Promise

import asyncio
from graphql_server import RequestParams, run_http_query

from .utils import as_dicts


def resolve_error_sync(_obj, _info):
    raise ValueError("error sync")


async def resolve_error_async(_obj, _info):
    await asyncio.sleep(0.001)
    raise ValueError("error async")


def resolve_field_sync(_obj, _info):
    return "sync"


async def resolve_field_async(_obj, info):
    await asyncio.sleep(0.001)
    return "async"


NonNullString = GraphQLNonNull(GraphQLString)

QueryRootType = GraphQLObjectType(
    name="QueryRoot",
    fields={
        "errorSync": GraphQLField(NonNullString, resolver=resolve_error_sync),
        "errorAsync": GraphQLField(NonNullString, resolver=resolve_error_async),
        "fieldSync": GraphQLField(NonNullString, resolver=resolve_field_sync),
        "fieldAsync": GraphQLField(NonNullString, resolver=resolve_field_async),
    },
)

schema = GraphQLSchema(QueryRootType)


def test_get_responses_using_asyncio_executor():
    class TestExecutor(AsyncioExecutor):
        called = False
        waited = False
        cleaned = False

        def wait_until_finished(self):
            TestExecutor.waited = True
            super().wait_until_finished()

        def clean(self):
            TestExecutor.cleaned = True
            super().clean()

        def execute(self, fn, *args, **kwargs):
            TestExecutor.called = True
            return super().execute(fn, *args, **kwargs)

    query = "{fieldSync fieldAsync}"

    loop = asyncio.get_event_loop()

    async def get_results():
        result_promises, params = run_http_query(
            schema,
            "get",
            {},
            dict(query=query),
            executor=TestExecutor(loop=loop),
            return_promise=True,
        )
        results = await Promise.all(result_promises)
        return results, params

    results, params = loop.run_until_complete(get_results())

    expected_results = [{"data": {"fieldSync": "sync", "fieldAsync": "async"}}]

    assert as_dicts(results) == expected_results
    assert params == [RequestParams(query=query, variables=None, operation_name=None)]
    assert TestExecutor.called
    assert not TestExecutor.waited
    assert TestExecutor.cleaned
