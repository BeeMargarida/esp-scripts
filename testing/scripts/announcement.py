import sys
import ujson
import ubinascii
import utime
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

    def __init__(self, client_id, capabilities):
        print("Starting up announcer...")
        self.mqtt_client = None
        self.mqtt_server = 'mosquitto'  # '10.250.7.209'
        self.client_id = client_id
        self.capabilities = capabilities

        config['ssid'] = 'Calou oh puto do andar de cima'
        config['wifi_pw'] = 'primodowilson'
        config['server'] = self.mqtt_server
        config['port'] = 1883
        if sys.platform != "linux":
            self.mqtt_client = MQTTClient(config)
        else:
            MQTTClient.DEBUG = True
            config['client_id'] = ubinascii.hexlify(client_id)
            self.mqtt_client = MQTTClient(**config)
            print(str(config))

        if sys.platform != "linux":
            logging.basicConfig(level=logging.INFO)

    async def run(self):
        data = dict(
            address=self.mqtt_client._addr,
            capabilities=self.capabilities
        )
        payload = dict(
            payload=data
        )
        await self.mqtt_client.publish("announcements", ujson.dumps(payload), qos = 1)