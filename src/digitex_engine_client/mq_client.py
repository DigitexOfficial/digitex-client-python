import sys
import asyncio
from functools import wraps

import aioamqp

from .client import Client
from .listener import Listener
from .auto_async import auto_async, auto_async_iter, synchonized

@auto_async_iter
class MqListener(Listener):
    def __init__(self, client, channel, queue_name, raw):
        self.client = client
        self.channel = channel
        self.raw = raw
        self.delivery_tag = None
        self.async_queue = asyncio.Queue()

        async def callback(channel, body, envelope, properties):
            self.async_queue.put_nowait((body, envelope.delivery_tag))

        asyncio.create_task(channel.basic_consume(
            callback,
            queue_name
        ))

    async def __anext__(self):
        msg, self.delivery_tag = await self.async_queue.get()
        if self.raw:
            return msg
        else:
            return self.client.parse_message(msg)

    @auto_async
    async def ack(self):
        if self.delivery_tag is None:
            return
        await self.channel.basic_client_ack(self.delivery_tag)
        self.delivery_tag = None

class MqClient(Client):
    """A connection to the engine that uses MQ as its transport."""

    def __init__(
        self, *args,
        prefetch_size=0, prefetch_count=0,
        target_exchange='', target_routing_key='engine.in.trade',
        **kwargs
    ):
        self.args = args
        self.kwargs = kwargs
        self.prefetch_size = prefetch_size
        self.prefetch_count = prefetch_count
        self.target_exchange = target_exchange
        self.target_routing_key = target_routing_key
        self.lock = None
        self.protocol = None
        self.transport = None
        self.channels = dict()

    @synchonized
    async def channel(self, kind):
        if kind in self.channels:
            return self.channels[kind]
        if self.protocol is None:
            self.transport, self.protocol = await aioamqp.connect(*self.args, **self.kwargs)
        channel = await self.protocol.channel()
        await channel.basic_qos(
            prefetch_count=self.prefetch_count,
            prefetch_size=self.prefetch_size,
            connection_global=False,
        )
        self.channels[kind] = channel
        return channel

    @auto_async
    async def close(self):
        if self.protocol is not None:
            await self.protocol.close()
        if self.transport is not None:
            self.transport.close()

    async def subscribe_to_exchange(self, exchange_name, queue_name=None, raw=False, durable=False):
        """
        Listen on the given exchange and yield received messages.

        This method sets up a new queue bound to the exchange
        and then returns a listener.
        """
        channel = await self.channel(exchange_name)
        if queue_name:
            queue = await channel.queue_declare(queue_name, durable=durable)
        else:
            queue = await channel.queue_declare('', exclusive=True, auto_delete=True)
        queue_name = queue['queue']
        await channel.queue_bind(queue_name, exchange_name, routing_key='#')
        return MqListener(self, channel, queue_name, raw)

    @auto_async
    async def subscribe_to_trading_events(self, queue_name=None, raw=False, durable=False):
        """Subscribe to events related to trading on this exchange."""
        return await self.subscribe_to_exchange('ex.engine.out.trade', queue_name, raw, durable=durable)

    @auto_async
    async def subscribe_to_market_data_events(self, queue_name=None, raw=False, durable=False):
        """Subscribe to events related to global market data."""
        return await self.subscribe_to_exchange('ex.engine.out.data', queue_name, raw, durable=durable)


    @auto_async
    async def send_encoded_message(self, encoded_message):
        """
        Send the given encoded message to the engine.

        This is a low-level method; normally instead of using this
        you'd call method representing possible messages on this
        client object directly.
        """
        channel = await self.channel('in')
        await channel.basic_publish(
            payload=encoded_message,
            exchange_name=self.target_exchange,
            routing_key=self.target_routing_key
        )
