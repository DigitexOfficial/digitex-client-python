import digitex_engine_client

client = digitex_engine_client.MqClient(host='192.168.88.33', login='digitex', password='t0mmylee919', virtualhost='/digitex')

client.order_book_request()

def normalize(decimal):
    return decimal.value64 / (10 ** decimal.scale)

listener = client.subscribe_to_market_data_events()
for message in listener:
    kind = message.WhichOneof("kontent")
    if kind == "order_book_msg":
        print('Last trade price:', normalize(message.order_book_msg.last_trade_price))
    elif kind == "order_book_updated_msg":
        print('Last trade price:', normalize(message.order_book_updated_msg.last_trade_price))
    elif kind == "exchange_rate_msg" and message.exchange_rate_msg.currency_pair_id == 1:
        print('Spot price:', normalize(message.exchange_rate_msg.mark_price))
    listener.ack()
