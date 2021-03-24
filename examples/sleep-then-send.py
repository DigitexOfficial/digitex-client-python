from time import sleep
from digitex_engine_client import *

client = MqClient(host='192.168.88.33', login='digitex', password='t0mmylee919', virtualhost='/digitex')

client.ping(trader_id=42)
sleep(5 * 60)
print('Pinging!')
client.ping(trader_id=42)
print('Pinged')
