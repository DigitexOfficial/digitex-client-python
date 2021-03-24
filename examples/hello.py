from digitex_engine_client import *

client = WsClient(host='ws.testnet.digitexfutures.com', token='your-api-key-here')

# Create a listener first so that we don't miss the reply.
listener = client.subscribe_to_trading_events()

client.ping(market_id=1)

message = next(listener)
print('Got', message)

client.close()
