import uuid
from datetime import datetime

import pytz

from . import messages_pb2
from .message_proxy import MessageProxy
from .auto_async import auto_async, should_use_sync


class Client:
    """
    A Digitex futures engine client.

    An instance of this type represents a connection
    to the engine that can be used to send and receive
    messages.

    This class itself is abstract; you need to instantiate
    one of its subclasses, either MqClient or TcpClient.
    """

    message_proxy = MessageProxy()

    @staticmethod
    def timestamp():
        """Make a microsecond timestamp as used in messages."""
        seconds = datetime.now(pytz.UTC).timestamp()
        return int(seconds * 1_000_000)

    def parse_message(self, data):
        """Parse a message from the given byte buffer."""
        message = messages_pb2.Message()
        message.ParseFromString(data)
        return message

    def encode_message(self, message):
        """Encode the given message to a byte buffer."""
        return message.SerializeToString()

    def send_message(self, message):
        """
        Send the given message to the engine.

        This is a low-level method; normally instead of using this
        you'd call method representing possible messages on this
        client object directly.
        """
        return self.send_encoded_message(self.encode_message(message))

    def close(self):
        """Close this client."""
        pass

    def __getattr__(self, name):
        """A hook enabling messages to be created, encoded and sent using simple calls."""
        try:
            make_message = getattr(Client.message_proxy, name)
        except AttributeError:
            class_name = type(self).__name__
            raise AttributeError('{!r} object has no attribute {!r}'.format(class_name, name)) from None

        def make_and_send_message(**kwargs):
            message = make_message(**kwargs)
            if not message.timestamp:
                message.timestamp = self.timestamp()
            if not message.client_id:
                message.client_id = uuid.uuid4().bytes

            if should_use_sync():
                self.send_message(message)
                return message

            async def future():
                await self.send_message(message)
                return message
            return future()

        return make_and_send_message
