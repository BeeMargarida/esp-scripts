import os
import gc
import sys
import logging
import ujson
from mqtt_as import config, MQTTClient
import uasyncio as asyncio


class Server():

    def __init__(self):
        print("Starting up server...")
        self.running_http = True
        self.running_script = False
        self.mqtt_client = None
        self.mqtt_server = '192.168.1.199'  # '10.250.7.209'

        config['ssid'] = 'Calou oh puto do andar de cima'
        config['wifi_pw'] = 'primodowilson'
        config['server'] = self.mqtt_server
        self.mqtt_client = MQTTClient(config)

        logging.basicConfig(level=logging.INFO)
        # logging.basicConfig(level=logging.DEBUG)

        self.run()

    def run(self):
        try:
            loop = asyncio.get_event_loop()
            self.server = asyncio.start_server(self.serve, "0.0.0.0", 80)
            self.server_task = loop.create_task(self.server)
            loop.run_forever()
        except Exception as e:
            print(e)

    async def failsafe(self):
        print("Starting failsafe")
        try:
            # cancel server task
            loop = asyncio.get_event_loop()
            await self.server_task.cancel()

            if self.mqtt_client.isconnected():
                await self.mqtt_client.disconnect()
            self.mqtt_client = None
            self.mqtt_client = MQTTClient(config)

            gc.collect()
            print("Starting up server...")
            self.server_task = loop.create_task(self.server)
        except TypeError:
            await asyncio.sleep(0)
            self.failsafe()

    async def delete_script(self):
        try:
            # delete previous script
            import script
            gc.collect()

            script.stop()
            os.remove("script.py")
            del sys.modules['script']

            if self.mqtt_client.isconnected():
                await self.mqtt_client.disconnect()

        except Exception as e:
            print("Script Delete Error")

    def serve(self, reader, writer):
        try:
            req = await reader.readline()
            req = req.decode("utf-8")
        except KeyboardInterrupt:
            raise OSError('Interrupt')
        except Exception as e:
            return

        request_info = req.find('GET /ping')
        if request_info != -1:
            print("GET /ping")
            data = {}
            data["status"] = 1
            data["running"] = self.running_script
            data_str = ujson.dumps(data)
            data_len = len(bytes(data_str, "utf-8"))
            await writer.awrite("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length:" + str(data_len) + "\r\n\r\n" + data_str)
            await asyncio.sleep(1)
            await writer.aclose()
            return

        request_info = req.find('POST /execute')
        if request_info == -1:
            await writer.awrite("HTTP/1.1 404\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot found")
            await asyncio.sleep(1)
            await writer.aclose()
            return

        # Get total length of script
        l = 0
        while True:
            h = await reader.readline()
            if not h or h == b'\r\n':
                break
            if 'Content-Length: ' in h:
                try:
                    l = int(h[16:-2])
                    print('Content Length is : ', l)
                except:
                    continue

        if l == 0:
            await writer.awrite("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nReceived file was empty.\r\n")
            await writer.aclose()
        else:
            try:
                read_l = 0
                postquery = b''
                while read_l < l:
                    tmp = await reader.read(l)
                    read_l += len(tmp)
                    postquery += tmp

            except MemoryError as e:
                print("Memory Error")
                await self.delete_script()

                await writer.awrite("HTTP/1.1 413\r\nContent-Type: text/html\r\n\r\n" + str(e) + "\r\n")
                await asyncio.sleep(1)
                await writer.aclose()

                loop = asyncio.get_event_loop()
                loop.create_task(self.failsafe())
                return

            try:
                # save script in .py file
                f = open("script.py", "w")
                f.write(postquery)
                f.close()
                gc.collect()

                print("File written!")

                # delete previous script
                await self.delete_script()

                # call and execute script
                import script

                self.mqtt_client._cb = script.on_input
                self.mqtt_client._connect_handler = script.conn_han

                # await asyncio.sleep(1)
                await self.mqtt_client.connect()

                print("MQTT Client Connected")

                # send HTTP response
                await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\nFile saved.\r\n")
                await writer.aclose()

                await script.exec(self.mqtt_client)

                self.running_script = True
                gc.collect()

            except MemoryError as e:
                print("Memory Error")
                await writer.awrite("HTTP/1.1 413\r\nContent-Type: text/html\r\n\r\n" + str(e) + "\r\n")
                await asyncio.sleep(1)
                await writer.aclose()
                
                loop = asyncio.get_event_loop()
                loop.create_task(self.failsafe())
                return
            except OSError as e:
                # Exception raised when MQTT Broker address is wrong
                yield from writer.awrite("HTTP/1.1 424\r\nContent-Type: text/html\r\n\r\n" + str(e) + "\r\n")
                yield from writer.aclose()
                return
            except Exception as e:
                print(e)
                await writer.awrite("HTTP/1.1 500\r\nContent-Type: text/html\r\n\r\n" + str(e) + "\r\n")
                await asyncio.sleep(1)
                await writer.aclose()
                return
        return
