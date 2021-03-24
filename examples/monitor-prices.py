import digitex_engine_client

# No authentication necessary!
client = digitex_engine_client.WsClient(host='ws.testnet.digitexfutures.com')

client.subscribe(market_id=1)
client.order_book_request()

def normalize(decimal):
    return decimal.value64 / (10 ** decimal.scale)

for message in client.subscribe_to_market_data_events():
    kind = message.WhichOneof("kontent")
    if kind == "order_book_msg":
        print(f'[market {message.market_id}] Last trade price:', normalize(message.order_book_msg.last_trade_price))
    elif kind == "order_book_updated_msg":
        print(f'[market {message.market_id}] Last trade price:', normalize(message.order_book_updated_msg.last_trade_price))
    elif kind == "exchange_rate_msg":
        print(f'[currency_pair {message.exchange_rate_msg.currency_pair_id}] Spot price:', normalize(message.exchange_rate_msg.mark_price))
