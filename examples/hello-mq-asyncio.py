import asyncio
from digitex_engine_client import *

client = MqClient(host='192.168.88.33', login='digitex', password='t0mmylee919', virtualhost='/digitex')

async def main():
    # Create a listener first so that we don't miss the reply.
    listener = await client.subscribe_to_trading_events()

    await client.ping(trader_id=42)

    message = await listener.__anext__()
    print('Got', message)

    await client.close()

asyncio.run(main())
