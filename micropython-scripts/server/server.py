import os
import gc
import sys
import logging
from mqtt_as import config, MQTTClient
import uasyncio as asyncio

mqtt_client = None
mqtt_server = '192.168.1.179'  # '10.250.7.209'

@asyncio.coroutine
def serve(reader, writer):
    global mqtt_client
    
    try:
        req = (yield from reader.readline())
        req = req.decode("utf-8")
    except KeyboardInterrupt:
        raise OSError('Interrupt')
    except Exception as e:
        return

    request_info = req.find('POST /execute')
    if request_info == -1:
        yield from writer.awrite("HTTP/1.0 404 OK\r\nContent-type: text/html\r\n\r\nFile saved.\r\n")
        yield from writer.aclose()
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
        yield from writer.awrite("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\nReceived file was empty.\r\n")
        yield from writer.aclose()
    else:
        postquery =  (yield from reader.readexactly(l))
        print(postquery)

        # Delete previous script
        try:
            import script
            os.remove("script.py")
            del sys.modules['script']
            gc.collect()
        except Exception as e:
            print("whoops")
            print(e)

        f = open("script.py", "w")
        f.write(postquery)
        f.close()

        print("File written!")

        yield from writer.awrite("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\nFile saved.\r\n")
        yield from writer.aclose()

        import script

        mqtt_client._cb= script.on_input
        mqtt_client._connect_handler = script.conn_han

        await mqtt_client.connect()

        script.exec(mqtt_client)
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
    loop = asyncio.get_event_loop()
    # mem_info()
    loop.create_task(asyncio.start_server(serve, "0.0.0.0", 80))
    loop.run_forever()
    loop.close()
