# Digitex engine client library

This library implements a client interface to the Digitex futures trading engine.

## Installation

First things first, you're going to need to install this library.

If you have the source code of this library in a local checkout, you may run
`pip3 install .` (where `.` is the path to the root directory of the library
checkout). Otherwise you may have luck running `pip3 install
digitex-engine-client` if you have the right repositories configured.

Whatever the source, Pip will automatically fetch the dependencies and build the
Protobuf definition. For this to work, you do need `protoc`, the Protobuf
compiler, to be installed on your machine (try using your distribution's
appropriate package). The build script (`setup.py`) will look for `protoc` in
the `PATH`; you can also specify the `protoc` location explicitly with the
`PROTOC` environment variable. If the script fails to find `protoc`, it will
raise an error right away.

## Connecting

The main API of the library is the abstract `Client` class, which represents a
connection to the engine backend, which serves as a proxy for the engine. The
concrete `WsClient` serves as an implementation of a client.

To connect to the engine, instantiate `WsClient`:

```python
client = WsClient(host='ws.mainnet.digitexfutures.com', token='your-api-key-here')
```

The host to use for testnet is `ws.testnet.digitexfutures.com`; for mainnet use
`ws.mainnet.digitexfutures.com`. For authentication, you can also pass a `bearer`
or a `session_id` instead of a `token`, depending on the type of key that you
have.

You can get a token over at https://exchange.digitexfutures.com/profile/api

To check if the connection is successful, ping the engine:

```python
client.ping()
```

## Messages

To interact with the exchange, a client can send and receive **messages**. The
exact messages that can be sent and received are defined in the `messages.proto`
file, which is compiled using `protoc` into the
`digitex_engine_client.messages_pb2` submodule.

It is thus possible to construct messages directly. For example, here's how one
can construct and send the ping message:

```python
from digitex_engine_client.messages_pb2 import *

message = Message(ping_msg=PingMessage())
client.send_message(message)
```

The library provides some shortcuts to make this more convenient. First, there's
a semi-public `message_proxy` that can be used to create messages in a more
natural way:

```python
message = client.message_proxy.ping()
client.send_message(message)
```

Any arguments that would have been passed to either the generic `Message`
constructor or a constructor of a specific message should be passed as arguments
into the `message_proxy` method.

Finally, it's possible to call the methods on a client object directly:

```python
client.ping()
```

This will do the following:


* Create the message using the specified arguments,
* Fill in generic fileds such as `client_id` and `timestamp` automatically,
unless they are set explicitly,
* Send the message by calling `send_message()`,
* Return the sent message (this is useful to e.g. note the generated
`client_id`).

See `messages.proto` for a complete description of supported messages, and read
`engine/API.md` for an in-depth explanation of their meanings.

## Listening

There are two streams of events you can listen on, the **trading** events and
the **market data** events, also known as *control* and *data* streams.

In order to listen for messages, use:

```python
for message in client.subscribe_to_trading_events():
    do_something_with(message)
```

And the same for `market_data` instead of `trading`.

It's necessary to call `digitex_engine_client.WsClient.subscribe()` before
trying to listen for market data events. The library will print a warning if you
forget to do this.

The object returned by the `subscribe_to_..._events()` methods is a
**listener**. You can use it directly as an iterator over received messages.

Please note that waiting for a message is a blocking operation. You should spawn
multiple threads in order to listen to multiple streams and send messages at the
same time.

## Sync or async

You can use the library in either sync or async manner. Using sync is
straightforward; using async means inserting `async` and `await` in a lot of
places, and relying on `asyncio` tasks instead of threads. Internally, the
WebSocket code always uses async code, and tries to transparently run it on a
background event loop if it detects you want to use it as sync.

## Examples

Please see the [examples](examples/) directory for a few examples, including a
simple bot that monitors the spot price and the last trade price and tries to
place orders.
