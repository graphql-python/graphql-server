"""GraphQL-Server
===================

GraphQL-Server is a base library that serves as a helper
for building GraphQL servers or integrations into existing web frameworks using
[GraphQL-Core](https://github.com/graphql-python/graphql-core).
"""

from .runtime import (
    execute,
    execute_sync,
    introspect,
    process_errors,
    subscribe,
    validate_document,
)
from .version import version, version_info

# The GraphQL-Server 3 version info.

__version__ = version
__version_info__ = version_info

__all__ = [
    "execute",
    "execute_sync",
    "introspect",
    "process_errors",
    "subscribe",
    "validate_document",
    "version",
    "version_info",
]
