from announcement import Announcer
from logstash import log_to_logstash
import uasyncio as asyncio
import os
import gc
import sys
import ujson
import ubinascii
import utime
import esp
from machine import unique_id
from mqtt_as import config, MQTTClient
import logging


class Server():

    def __init__(self, client_id, ip, capabilities):
        print("Starting up server...")
        self.running_script = 0
        self.mqtt_client = None
        self.mqtt_client_metrics = None
        self.mqtt_server = '192.168.1.227'  # '10.250.7.209'
        self.memory_error = False
        self.assigned_nodes = ""
        self.start_time = utime.ticks_ms()
        self.last_payload = 0
        self.last_payload_id = None
        self.client_id = client_id
        self.ip = ip
        self.capabilities = capabilities
        self.client_id = unique_id()

        announcer = Announcer(self.client_id, self.ip, self.capabilities, 0)
        asyncio.run(announcer.run())

        config['ssid'] = '-'
        config['wifi_pw'] = '-'
        config['server'] = self.mqtt_server
        config['port'] = 1883

        MQTTClient.DEBUG = True

        config['client_id'] = ubinascii.hexlify(unique_id())
        self.mqtt_client = MQTTClient(config)

        config['client_id'] = ubinascii.hexlify(str(unique_id()) + "metrics")
        self.mqtt_client_metrics = MQTTClient(config)

        logging.basicConfig(level=logging.INFO)

        self.run()

    def run(self):
        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(self.handle_exceptions)

            self.metrics_task = loop.create_task(self.metrics())
            self.server = asyncio.start_server(self.serve, "0.0.0.0", 80)
            self.server_task = loop.create_task(self.server)
            loop.create_task(log_to_logstash({
                "@tags": ["micropython", self.capabilities[0]],
                "@message": {"message": "Started server"}
            }))
            loop.run_forever()
        except Exception as e:
            print(e)

    def handle_exceptions(self, loop, context):
        exception = context['exception']
        if type(exception) == type(MemoryError()):
            print("Memory Error")

            self.memory_error = True

            loop = asyncio.get_event_loop()
            loop.create_task(self.failsafe(True))
            return

    async def metrics(self):
        while True:
            try:
                if not self.mqtt_client_metrics._isconnected:
                    await self.mqtt_client_metrics.connect()
                else:
                    current_time = utime.ticks_ms()
                    await self.mqtt_client_metrics.publish(
                        "telemetry/%s/uptime" % self.ip, str(utime.ticks_diff(current_time, self.start_time)), qos=0)

                    if self.last_payload_id:
                        await self.mqtt_client_metrics.publish(
                            "telemetry/%s/%s/last_payload" % (self.ip, self.last_payload_id), str(self.last_payload), qos=0)

                    await self.mqtt_client_metrics.publish(
                        "telemetry/%s/free_ram" % self.ip, str(gc.mem_free()), qos=0)

                    await self.mqtt_client_metrics.publish(
                        "telemetry/%s/alloc_ram" % self.ip, str(gc.mem_alloc()), qos=0)

                    await self.mqtt_client_metrics.publish(
                        "telemetry/%s/running" % self.ip, str(self.running_script), qos=0)

                    nr_nodes = len(self.assigned_nodes.split(" "))
                    if self.assigned_nodes == "":
                        nr_nodes = 0
                    assigned_nodes_dict = dict(
                        nodes=str(self.assigned_nodes),
                        nr=str(nr_nodes)
                    )
                    await self.mqtt_client_metrics.publish(
                        "telemetry/%s/nodes" % self.ip, ujson.dumps(assigned_nodes_dict), qos=0)

                    # await self.mqtt_client_metrics.publish(
                    #     "telemetry/%s/info" % self.client_id, os.uname(), qos=1)

                    # if sys.platform != "linux":
                    #     await self.mqtt_client_metrics.publish(
                    #         "telemetry/%s/flash_size" % self.ip, str(esp.flash_size()), qos=0)
                    # else:
                    info = os.statvfs("/")
                    flash_size = (info[4] * info[1]) / 1024
                    await self.mqtt_client_metrics.publish(
                        "telemetry/%s/flash_size" % self.ip, str(flash_size), qos=0)

                    await asyncio.sleep(5)
            except Exception as e:
                print(e)
        return

    async def failsafe(self, announce):
        print("Starting failsafe")
        loop = asyncio.get_event_loop()
        try:
            loop.create_task(log_to_logstash({
                "@tags": ["micropython", self.capabilities[0]],
                "@message": {"message": "Starting failsafe"}
            }))
            # cancel script task
            if self.script_task:
                self.script_task.cancel()

            # cancel server task
            self.server.close()
            self.server_task.cancel()

            if self.mqtt_client.isconnected():
                await self.mqtt_client.disconnect()
            self.mqtt_client = None

            config['client_id'] = ubinascii.hexlify(unique_id())
            self.mqtt_client = MQTTClient(config)

            self.memory_error = False
            self.assigned_nodes = ""

            print("Starting up server...")
            self.start_time = utime.ticks_ms()
            self.server_task = loop.create_task(self.server)

            if announce:
                announcer = Announcer(self.client_id, self.ip,
                                      self.capabilities, 1)
                await announcer.run()
        except TypeError as e:
            print("FAILSAFE EXCEPTION")
            print(e)
            await asyncio.sleep(0)
            loop.create_task(self.failsafe(True))

    async def delete_script(self):
        try:
            # delete previous script
            import script

            if hasattr(script, "stop"):
                script.stop()
            del sys.modules['script']
        except Exception as e:
            print("Script Removing Error")
            print(e)

        try:
            os.remove("./script.py")
        except Exception as e:
            print("Script Delete Error")
            print(e)

        if self.mqtt_client.isconnected():
            await self.mqtt_client.disconnect()

        await asyncio.sleep(0.2)
        return

    async def serve(self, reader, writer):
        if(self.memory_error):
            return

        try:
            req = await reader.readline()
            req = req.decode("utf-8")
        except Exception as e:
            return

        request_info = req.find('GET /ping')
        if request_info != -1:
            print("GET /ping")
            req = await reader.read(256)
            writer.write("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOk.\r\n")
            await writer.drain()
            await writer.aclose()
            return

        request_info = req.find('POST /execute')
        if request_info == -1:
            await writer.awrite("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot found.\r\n")
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
                self.last_payload = str(l)
                self.last_payload_id = str(utime.ticks_ms())

                # delete previous script
                await self.delete_script()

                if sys.platform != "linux":
                    # save script in .py file
                    f = open("script.py", "w")
                    read_l = 0
                    while read_l < l:
                        tmp = await reader.read(l)
                        read_l += len(tmp)
                        f.write(tmp)
                    f.close()
                else:
                    f = open("script.py", "w")
                    read_l = 0
                    postquery = b''
                    while read_l < l:
                        tmp = await reader.read(l)
                        read_l += len(tmp)
                        postquery += tmp
                    f.write(postquery)
                    f.close()

            except MemoryError as e:
                print("Memory Error on write")
                f.close()
                await writer.awrite("HTTP/1.1 413 Request Entity Too Large\r\nContent-Type: text/plain\r\n\r\n" + str(e) + "\r\n")
                await writer.aclose()

                self.memory_error = True
                loop = asyncio.get_event_loop()
                loop.create_task(self.failsafe(False))
                return
            except Exception as e:
                print("Write exception")
                print(e)
                print(e.args[0])
                return

            try:
                print("File written!")

                # call and execute script
                import script

                self.mqtt_client._cb = script.on_input
                self.mqtt_client._connect_handler = script.conn_han

                await self.mqtt_client.connect()

                self.assigned_nodes = script.get_nodes()

                print("MQTT Client Connected")

                loop = asyncio.get_event_loop()
                loop.create_task(log_to_logstash({
                    "@tags": ["micropython", self.capabilities[0]],
                    "@message": {"message": "Script written and MQTT connected"}
                }))

                # send HTTP response
                await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\nFile saved.\r\n")
                await writer.aclose()

                self.script_task = loop.create_task(script.exec(
                    self.mqtt_client, self.capabilities))

                self.running_script = 1

            except MemoryError as e:
                print("Memory Error")
                await writer.awrite("HTTP/1.1 413 Request Entity Too Large\r\nContent-Type: text/plain\r\n\r\n" + str(e) + "\r\n")
                await writer.aclose()

                loop = asyncio.get_event_loop()
                loop.create_task(self.failsafe(False))
                return
            except OSError as e:
                print("OSERROR: " + str(e))
                # Exception raised when MQTT Broker address is wrong
                await writer.awrite("HTTP/1.1 424\r\nContent-Type: text/html\r\n\r\n" + str(e) + "\r\n")
                await writer.aclose()
                return
            except Exception as e:
                print("EXCEPTION")
                print(e)
                del sys.modules['script']
                os.remove("script.py")

                await writer.awrite("HTTP/1.1 500\r\nContent-Type: text/html\r\n\r\n" + str(e) + "\r\n")
                await writer.aclose()
                return
        return
