import asyncio
from digitex_engine_client import *

client = MqClient(host='192.168.88.33', login='digitex', password='t0mmylee919', virtualhost='/digitex')

async def main():
    await client.ping(trader_id=42)
    await asyncio.sleep(5 * 60)
    print('Pinging!')
    await client.ping(trader_id=42)
    print('Pinged')

asyncio.run(main())
