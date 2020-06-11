# This file is executed on every boot (including wake-boot from deepsleep)
from mqtt_as import config, MQTTClient
from machine import unique_id
import uasyncio as asyncio
import ubinascii
import network

loop = asyncio.get_event_loop()

def sub_cb(topic, msg, retained):
    loop.create_task(publish(msg))
    
async def publish(msg):
    await client.publish('t4', msg, qos=1)

async def conn_han(client):
    await client.subscribe('t3', 1)

def main(client):
    await client.connect()
    while True:
        await asyncio.sleep(1)

config['ssid'] = ''
config['wifi_pw'] = ''
config['server'] = ''
config['port'] = 1883
config['client_id'] = ubinascii.hexlify(unique_id())
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han

client = MQTTClient(config)

try:
    loop.run_until_complete(main(client))
finally:
    client.close()

