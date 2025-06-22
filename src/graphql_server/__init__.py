"""
GraphQL-Server
===================

GraphQL-Server is a base library that serves as a helper
for building GraphQL servers or integrations into existing web frameworks using
[GraphQL-Core](https://github.com/graphql-python/graphql-core).
"""

from .runtime import (
    execute,
    execute_sync,
    subscribe,
    validate_document,
    process_errors,
    introspect,
)
from .version import version, version_info

# The GraphQL-Server 3 version info.

__version__ = version
__version_info__ = version_info

__all__ = [
    "version",
    "version_info",
    "execute",
    "execute_sync",
    "subscribe",
    "validate_document",
    "process_errors",
    "introspect",
]
