import sys
import ujson
import ubinascii
import utime
import socket
if sys.platform != "linux":
    import esp
    from machine import unique_id
    from mqtt_as import config, MQTTClient
else:
    from mqtt_as import MQTTClient
    from config import config
if sys.platform != "linux":
    import logging

class Announcer():

    def __init__(self, client_id, ip, capabilities, failure):
        print("Starting up announcer...")
        self.mqtt_client = None
        self.mqtt_server = '192.168.1.227'  # '10.250.7.209'
        self.client_id = client_id
        self.ip = ip
        self.capabilities = capabilities
        self.failure = failure

        config['ssid'] = '-'
        config['wifi_pw'] = '-'
        config['server'] = self.mqtt_server
        config['port'] = 1883
        config['client_id'] = ubinascii.hexlify(str(unique_id()) + "announcements")

        self.mqtt_client = MQTTClient(config)
        logging.basicConfig(level=logging.INFO)

    async def run(self):
        await self.mqtt_client.connect()

        data = dict(
            address=self.ip,
            capabilities=self.capabilities,
            failure=self.failure
        )
        payload = dict(
            payload=data
        )
        print("Announcing: " + ujson.dumps(payload))
        await self.mqtt_client.publish("announcements/" + self.ip, ujson.dumps(payload), qos = 1, retain = True)

        await self.mqtt_client.disconnect()