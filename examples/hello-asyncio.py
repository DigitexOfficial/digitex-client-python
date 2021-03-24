import asyncio
from digitex_engine_client import *

client = WsClient(host='ws.testnet.digitexfutures.com', token='your-api-key-here')

async def main():
    # Create a listener first so that we don't miss the reply.
    listener = await client.subscribe_to_trading_events()

    await client.ping(market_id=1)

    message = await listener.__anext__()
    print('Got', message)

    await client.close()

asyncio.run(main())
