from __future__ import annotations

import asyncio

import pytest

from graphql_server.channels.handlers.base import ChannelsConsumer


class DummyChannelLayer:
    def __init__(self) -> None:
        self.added: list[tuple[str, str]] = []
        self.discarded: list[tuple[str, str]] = []

    async def group_add(self, group: str, channel: str) -> None:
        self.added.append((group, channel))

    async def group_discard(self, group: str, channel: str) -> None:
        self.discarded.append((group, channel))


@pytest.mark.asyncio
async def test_channel_listen_receives_messages_and_cleans_up() -> None:
    consumer = ChannelsConsumer()
    layer = DummyChannelLayer()
    consumer.channel_layer = layer
    consumer.channel_name = "chan"

    gen = consumer.channel_listen("test.message", groups=["g"], timeout=0.1)

    async def send() -> None:
        await asyncio.sleep(0)
        queue = next(iter(consumer.listen_queues["test.message"]))
        queue.put_nowait({"type": "test.message", "payload": 1})

    asyncio.create_task(send())

    with pytest.deprecated_call(match="Use listen_to_channel instead"):
        message = await gen.__anext__()
    assert message == {"type": "test.message", "payload": 1}

    await gen.aclose()

    assert layer.added == [("g", "chan")]
    assert layer.discarded == [("g", "chan")]


@pytest.mark.asyncio
async def test_channel_listen_times_out() -> None:
    consumer = ChannelsConsumer()
    layer = DummyChannelLayer()
    consumer.channel_layer = layer
    consumer.channel_name = "chan"

    gen = consumer.channel_listen("test.message", groups=["g"], timeout=0.01)

    with pytest.deprecated_call(match="Use listen_to_channel instead"):
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    assert layer.added == [("g", "chan")]
    assert layer.discarded == [("g", "chan")]
