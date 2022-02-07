from typing import Any, Dict, List, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from .contstants import (
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_ACK,
    GQL_PING,
    GQL_PONG,
    GQL_SUBSCRIBE,
    GQL_NEXT,
    GQL_ERROR,
    GQL_COMPLETE,
)


class ConnectionInitMessage(TypedDict):
    """
    Direction: Client -> Server
    """

    payload: Optional[Dict[str, Any]]
    type = GQL_CONNECTION_INIT


class ConnectionAckMessage(TypedDict):
    """
    Direction: Server -> Client
    """

    payload: Optional[Dict[str, Any]]
    type = GQL_CONNECTION_ACK


class PingMessage(TypedDict):
    """
    Direction: bidirectional
    """

    payload: Optional[Dict[str, Any]]
    type = GQL_PING


class PongMessage(TypedDict):
    """
    Direction: bidirectional
    """

    payload: Optional[Dict[str, Any]]
    type = GQL_PONG


class SubscribeMessagePayload(TypedDict):
    query: str
    operationName: Optional[str]
    variables: Optional[Dict[str, Any]]
    extensions: Optional[Dict[str, Any]]


class SubscribeMessage(TypedDict):
    """
    Direction: Client -> Server
    """

    id: str
    payload: SubscribeMessagePayload
    type = GQL_SUBSCRIBE


class NextMessage(TypedDict):
    """
    Direction: Server -> Client
    """

    id: str
    payload: Dict[str, Any]  # TODO: shape like ExecutionResult
    type = GQL_NEXT


class ErrorMessage(TypedDict):
    """
    Direction: Server -> Client
    """

    id: str
    payload: List[Dict[str, Any]]  # TODO: shape like List[GraphQLError]
    type = GQL_ERROR


class CompleteMessage(TypedDict):
    """
    Direction: bidirectional
    """

    type = GQL_COMPLETE

    id: str
