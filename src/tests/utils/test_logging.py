import logging

from graphql.error import GraphQLError

from graphql_server.utils.logs import GraphQLServerLogger


def test_graphql_server_logger_error(caplog):
    caplog.set_level(logging.ERROR, logger="graphql_server.execution")

    exc = GraphQLError("test exception")
    GraphQLServerLogger.error(exc)

    assert caplog.record_tuples == [
        ("graphql_server.execution", logging.ERROR, "test exception")
    ]
