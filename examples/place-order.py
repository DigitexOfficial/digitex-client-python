import digitex_engine_client
from digitex_engine_client.messages_pb2 import *

client = digitex_engine_client.WsClient(host='ws.testnet.digitexfutures.com', token='your-api-key-here')

# Create a listener first so that we don't miss the reply.
listener = client.subscribe_to_trading_events()

client.place_order(
    market_id=1,
    order_type=LIMIT,
    side=BUY,
    duration=GTC,
    price=Decimal(value64=10260_0000, scale=4),
    quantity=Decimal(value64=100, scale=0)
)

message = next(listener)
print('Got', message)
