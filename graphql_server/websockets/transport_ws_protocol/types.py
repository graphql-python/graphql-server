from typing import Any, Dict, List, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from dataclasses import dataclass, asdict

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


class Message:
    def asdict(self):
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass
class ConnectionInitMessage(Message):
    """
    Direction: Client -> Server
    """

    payload: Optional[Dict[str, Any]] = None
    type: str = GQL_CONNECTION_INIT


@dataclass
class ConnectionAckMessage(Message):
    """
    Direction: Server -> Client
    """

    payload: Optional[Dict[str, Any]] = None
    type: str = GQL_CONNECTION_ACK


@dataclass
class PingMessage(Message):
    """
    Direction: bidirectional
    """

    payload: Optional[Dict[str, Any]] = None
    type: str = GQL_PING


@dataclass
class PongMessage(Message):
    """
    Direction: bidirectional
    """

    payload: Optional[Dict[str, Any]] = None
    type: str = GQL_PONG


@dataclass
class SubscribeMessagePayload(Message):
    query: str
    operationName: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    extensions: Optional[Dict[str, Any]] = None


@dataclass
class SubscribeMessage(Message):
    """
    Direction: Client -> Server
    """

    id: str
    payload: SubscribeMessagePayload
    type: str = GQL_SUBSCRIBE

    @classmethod
    def from_dict(cls, message: dict):
        subscribe_message = cls(**message)
        subscribe_message.payload = SubscribeMessagePayload(**subscribe_message.payload)
        return subscribe_message


@dataclass
class NextMessage(Message):
    """
    Direction: Server -> Client
    """

    id: str
    payload: Dict[str, Any]  # TODO: shape like ExecutionResult
    type: str = GQL_NEXT


@dataclass
class ErrorMessage(Message):
    """
    Direction: Server -> Client
    """

    id: str
    payload: List[Dict[str, Any]]  # TODO: shape like List[GraphQLError]
    type: str = GQL_ERROR


@dataclass
class CompleteMessage(Message):
    """
    Direction: bidirectional
    """

    id: str
    type: str = GQL_COMPLETE
