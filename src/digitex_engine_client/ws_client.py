import sys
import asyncio

import aiohttp

from .client import Client
from .listener import Listener
from .auto_async import auto_async, auto_async_iter, synchonized

@auto_async_iter
class WsListener(Listener):
    def __init__(self, client, ws):
        self.client = client
        self.ws = ws

    async def __anext__(self):
        msg = await self.ws.receive()
        if msg.type == aiohttp.WSMsgType.CLOSE or msg.type >= 0x100:
            raise StopAsyncIteration()
        return self.client.parse_message(msg.data)


class WsClient(Client):
    """A connection to the engine that uses a WebSocket to the backend as its transport."""

    def __init__(self, host='ws.mainnet.digitexfutures.com', port=443, token=None, session_id=None, bearer=None):
        assert not host.endswith('/')
        assert not host.startswith('http://') and not host.startswith('https://')
        if not host.startswith('ws://') and not host.startswith('wss://'):
            host = 'wss://' + host
        self.url = '{}:{}/events/'.format(host, port)

        self.token = token
        self.session_id = session_id
        self.bearer = bearer
        self.session = None
        self.ws = dict()
        self.lock = None
        self.has_subscribed = False

    @synchonized
    async def ensure_ws(self, kind='order'):
        if kind in self.ws:
            return self.ws[kind]

        if self.session is None:
            self.session = aiohttp.ClientSession()
        url = self.url + kind + '/'

        extra_headers = dict()
        if self.bearer is not None:
            extra_headers['Authorization'] = 'Bearer ' + self.bearer
        if self.token is not None:
            extra_headers['Authorization'] = 'Token ' + self.token
        if self.session_id is not None:
            extra_headers['Cookie'] = 'sessionid=' + self.session_id

        ws = await self.session.ws_connect(url, headers=extra_headers, heartbeat=30)
        self.ws[kind] = ws
        return ws

    @auto_async
    async def close(self):
        if self.session is not None:
            await self.session.close()

    @auto_async
    async def subscribe_to_trading_events(self):
        """Subscribe to events related to trading on this exchange."""
        ws = await self.ensure_ws()
        return WsListener(self, ws)

    @auto_async
    async def subscribe_to_market_data_events(self):
        """Subscribe to events related to global market data."""
        if not self.has_subscribed:
            print(
                "Warning: when using the WebSocket backend, you will not receive"
                " any market data events unless you call subscribe()",
                file=sys.stderr
            )
        ws = await self.ensure_ws('marketdata')
        return WsListener(self, ws)

    def subscribe(self, market_id, subscribe_mask=0b1111, unsubscribe_mask=0):
        self.has_subscribed = True
        msg = self.message_proxy.subscribe(
            market_id=market_id,
            subscribe_mask=subscribe_mask,
            unsubscribe_mask=unsubscribe_mask
        )
        msg = self.encode_message(msg)
        return self.send_encoded_message(msg, kind='marketdata')

    @auto_async
    async def send_encoded_message(self, encoded_message, kind='order'):
        """
        Send the given encoded message to the engine.

        This is a low-level method; normally instead of using this
        you'd call method representing possible messages on this
        client object directly.
        """
        ws = await self.ensure_ws(kind)
        async with self.lock:
            await ws.send_bytes(encoded_message)
