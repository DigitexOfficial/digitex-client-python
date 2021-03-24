from digitex_engine_client import *

client = MqClient(host='192.168.88.33', login='digitex', password='t0mmylee919', virtualhost='/digitex')

# Create a listener first so that we don't miss the reply.
listener = client.subscribe_to_trading_events()

client.ping(market_id=1, trader_id=42)

message = next(listener)
print('Got', message)

client.close()
