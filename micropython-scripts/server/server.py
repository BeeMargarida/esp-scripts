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
        self.mqtt_server = '192.168.1.179'  # '10.250.7.209'

        config['ssid'] = 'Calou oh puto do andar de cima'
        config['wifi_pw'] = 'primodowilson'
        config['server'] = self.mqtt_server
        self.mqtt_client = MQTTClient(config)

        logging.basicConfig(level=logging.INFO)
        # logging.basicConfig(level=logging.DEBUG)

        self.loop = asyncio.get_event_loop(runq_len=64, waitq_len=64)
        self.server = asyncio.start_server(self.serve, "0.0.0.0", 80)
        self.loop.create_task(self.server)
        self.loop.run_forever()
        self.loop.close()

    @asyncio.coroutine
    def serve(self, reader, writer):
        try:
            req = (yield from reader.readline())
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
            await asyncio.sleep(0.5)
            await writer.aclose()
            return

        request_info = req.find('POST /execute')
        if request_info == -1:
            await writer.awrite("HTTP/1.1 404\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot found")
            await asyncio.sleep(0.5)
            await writer.aclose()
            return

        l = 0
        while self.running_http:
            h = (yield from reader.readline())
            if not h or h == b'\r\n':
                break
            if 'Content-Length: ' in h:
                try:
                    l = int(h[16:-2])
                    print('Content Length is : ', l)
                except:
                    continue

        if l == 0:
            yield from writer.awrite("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nReceived file was empty.\r\n")
            yield from writer.aclose()
        else:
            try:
                postquery = (yield from reader.readexactly(l))

                # delete previous script
                import script
                gc.collect()

                script.stop()
                os.remove("script.py")
                del sys.modules['script']
                self.mqtt_client.disconnect()

                # save script in .py file
                f = open("script.py", "w")
                f.write(postquery)
                f.close()
                gc.collect()

                print("File written!")

                # send HTTP response
                yield from writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\nFile saved.\r\n")
                yield from writer.aclose()

                # call and execute script
                import script
                gc.collect()

                self.mqtt_client._cb = script.on_input
                self.mqtt_client._connect_handler = script.conn_han

                await asyncio.sleep(0.5)
                await self.mqtt_client.connect()

                await script.exec(self.mqtt_client)

                self.running_script = True
                gc.collect()

            except MemoryError as e:
                print(e)
                yield from writer.awrite("HTTP/1.1 500\r\nContent-Type: text/html\r\n\r\n" + str(e) + "\r\n")
                yield from writer.aclose()
                self.running_http = False
            except Exception as e:
                print("whoops")
                print(e)

        print("HERE")
        self.failsafe()
        return

    def failsafe(self):
        print("Starting failsafe...")
        try:
            # self.server.close()
            self.loop.stop()
            self.loop.close()
            self.mqtt_client.disconnect()
            
            self.loop = None
            self.mqtt_client = None
            self.server = None

            print("After closing loop")
            gc.collect()
            self.__init__()
        except Exception as e:
            print(e)
