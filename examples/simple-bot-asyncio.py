import random
import asyncio

import digitex_engine_client
from digitex_engine_client.messages_pb2 import *

client = digitex_engine_client.WsClient(host='ws.testnet.digitexfutures.com', token='your-api-key-here')

spot_price = None
last_trade_price = None
position_side = SIDE_UNDEFINED


def round_price(price):
    tick_size = 5_0000
    return round(price / tick_size) * tick_size


async def place_an_order():
    if spot_price is None or last_trade_price is None:
        print('Skipped placing an order due to unknown price')
        return

    quantity = random.randint(100, 1000)
    rounded_spot_price = round_price(spot_price.value64)

    if rounded_spot_price < last_trade_price.value64:
        side = SELL
    elif rounded_spot_price > last_trade_price.value64:
        side = BUY
    else:
        if position_side == LONG:
            side = SELL
        elif position_side == SHORT:
            side = BUY
        else:
            side = random.choice([BUY, SELL])

    print(f'Placing an order for {quantity} at {rounded_spot_price}')
    await client.place_order(
        market_id=1,
        order_type=LIMIT,
        side=side,
        duration=GTC,
        price=Decimal(value64=rounded_spot_price, scale=4),
        quantity=Decimal(value64=quantity, scale=0)
    )


async def listen_for_trading_events():
    global position_side

    async for message in await client.subscribe_to_trading_events():
        if message.error_code != 0:
            print(message)
        kind = message.WhichOneof("kontent")
        if kind == "order_filled_msg":
            position_side = message.order_filled_msg.trades[0].position


async def listen_for_market_data_events():
    global spot_price
    global last_trade_price

    async for message in await client.subscribe_to_market_data_events():
        kind = message.WhichOneof("kontent")
        if kind == "order_book_msg":
            last_trade_price = message.order_book_msg.last_trade_price
        elif kind == "order_book_updated_msg":
            last_trade_price = message.order_book_updated_msg.last_trade_price
        elif kind == "exchange_rate_msg" and message.exchange_rate_msg.currency_pair_id == 1:
            spot_price = message.exchange_rate_msg.mark_price

        if spot_price is not None and last_trade_price is not None:
            if round_price(spot_price.value64) != last_trade_price.value64:
                # Better act fast!
                await place_an_order()

async def main():
    await client.subscribe(market_id=1)
    await client.order_book_request()

    asyncio.create_task(listen_for_market_data_events())
    asyncio.create_task(listen_for_trading_events())

    while True:
        await asyncio.sleep(5)
        await place_an_order()

asyncio.run(main())
