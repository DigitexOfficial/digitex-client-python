import socket
from .client import Client
from .listener import Listener


class TcpListener(Listener):
    def __init__(self, client, stream):
        self.client = client
        self.stream = stream

    def __next__(self):
        size = self.client.read_uleb128(self.stream)
        if size is None:
            raise StopIteration()
        data = self.client.read_exact(self.stream, size)
        if data is None:
            raise StopIteration()
        return self.client.parse_message(data)


class TcpClient(Client):
    """A connection to the engine that uses TCP as its transport."""

    def __init__(self, in_trade_addr, out_trade_addr, out_data_addr):
        self._in_trade = socket.create_connection(in_trade_addr)
        self._out_trade = socket.create_connection(out_trade_addr)
        self._out_data = socket.create_connection(out_data_addr)

    def close(self):
        self._in_trade.close()
        self._out_trade.close()
        self._out_data.close()

    def read_exact(self, stream, size):
        """
        Read exactly the given number of bytes from the given stream.

        On EOF, returns None.
        """
        buffer = bytearray()
        while len(buffer) < size:
            b = stream.recv(size - len(buffer))
            if not b:
                return None
            buffer.extend(b)
        return bytes(buffer)

    def write_exact(self, stream, data):
        """Write exactly the given number of bytes to the given stream."""
        i = 0
        while i < len(data):
            wrote = stream.send(data[i:])
            i += wrote

    def read_uleb128(self, stream):
        """Read an ULEB128-encoded number from the given stream."""
        value = 0
        shift = 0
        b = 128
        while b & 128:
            b = self.read_exact(stream, 1)
            if not b:
                return None
            b = b[0]
            value |= (b & ~128) << shift
            shift += 7
        return value

    def write_uleb128(self, stream, value):
        """Encode the given number into ULEB128 and write it into the given stream."""
        buffer = bytearray()
        while value > 127:
            b = value & 127
            value >>= 7
            b |= 128
            buffer.append(b)
        buffer.append(value)
        self.write_exact(stream, buffer)

    def subscribe_to_trading_events(self):
        """Subscribe to events related to trading on this exchange."""
        return TcpListener(self, self._out_trade)

    def subscribe_to_market_data_events(self):
        """Subscribe to events related to global market data."""
        return TcpListener(self, self._out_data)

    def send_encoded_message(self, encoded_message):
        """
        Send the given encoded message to the engine.

        This is a low-level method; normally instead of using this
        you'd call method representing possible messages on this
        client object directly.
        """
        self.write_uleb128(self._in_trade, len(encoded_message))
        self.write_exact(self._in_trade, encoded_message)
