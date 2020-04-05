import os
import gc
import sys
import logging
import ujson
from mqtt_as import config, MQTTClient
import uasyncio as asyncio

mqtt_client = None
mqtt_server = '192.168.1.179'  # '10.250.7.209'
running_script = False

@asyncio.coroutine
def serve(reader, writer):
    global mqtt_client
    global running_script

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
        data["running"] = running_script
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
    while True:
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
        postquery = (yield from reader.readexactly(l))

        # Delete previous script
        try:
            import script
            script.stop()
            os.remove("script.py")
            del sys.modules['script']
            mqtt_client.disconnect()
            gc.collect()
        except Exception as e:
            print("whoops")
            print(e)

        f = open("script.py", "w")
        f.write(postquery)
        f.close()
        gc.collect()

        print("File written!")

        yield from writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\nFile saved.\r\n")
        yield from writer.aclose()

        import script
        gc.collect()

        mqtt_client._cb = script.on_input
        mqtt_client._connect_handler = script.conn_han
        
        await asyncio.sleep(0.5)
        await mqtt_client.connect()
        
        await script.exec(mqtt_client)

        running_script = True
        gc.collect()


def start():
    global loop
    global mqtt_client

    # Setup MQTT Client
    config['ssid'] = 'Calou oh puto do andar de cima'
    config['wifi_pw'] = 'primodowilson'
    config['server'] = mqtt_server
    mqtt_client = MQTTClient(config)

    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop(runq_len=64, waitq_len=64)
    # mem_info()
    loop.create_task(asyncio.start_server(serve, "0.0.0.0", 80))
    loop.run_forever()
    loop.close()
