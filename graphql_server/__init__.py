"""
GraphQL-Server
===================

GraphQL-Server is a base library that serves as a helper for building GraphQL
servers or integrations into existing web frameworks using
`GraphQL-Core-3`_

.. _GraphQL-Core-3: https://github.com/graphql-python/graphql-core).
"""

from graphql.error import format_error as format_error_default

from .error import HttpQueryError
from .graphql_server import (
    GraphQLParams,
    GraphQLResponse,
    ServerResponse,
    encode_execution_results,
    format_execution_result,
    json_encode,
    json_encode_pretty,
    load_json_body,
    run_http_query,
)
from .version import version, version_info

# The GraphQL-Server 3 version info.

__version__ = version
__version_info__ = version_info

__all__ = [
    "version",
    "version_info",
    "run_http_query",
    "encode_execution_results",
    "load_json_body",
    "json_encode",
    "json_encode_pretty",
    "HttpQueryError",
    "GraphQLParams",
    "GraphQLResponse",
    "ServerResponse",
    "format_execution_result",
    "format_error_default",
]
