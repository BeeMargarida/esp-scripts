import socket
from machine import Pin
import os
import machine
import ubinascii
import mqtt
import sys

mqtt_client = None
client_id = ubinascii.hexlify(machine.unique_id())
mqtt_server = '192.168.1.179' #'10.250.7.209'

def qs_parse(query):

    parameters = {}
    qs = query.split("?")
    if len(qs) < 2:
        return parameters

    qs = qs[1]
    ampersandSplit = qs.split("&")

    for element in ampersandSplit:
        equalSplit = element.split("=")
        parameters[equalSplit[0]] = equalSplit[1]

    return parameters


def start(topic_pub):
    global mqtt_client

    led = Pin(0, Pin.OUT)
    led.on()
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

    sck = socket.socket()
    sck.bind(addr)
    sck.listen(1)

    print('listening on', addr)

    while True:
        try:
            conn, addr = sck.accept()
            req = conn.readline()
            req = req.decode("utf-8")
        except KeyboardInterrupt:
            raise OSError('Interrupt')
        except Exception as e:
            print(e)
            return

        request_info = req.find('POST /execute')
        if request_info == -1:
            conn.send('HTTP/1.0 404 Not Found\r\nContent-type: text/html\r\n\r\n')
            conn.close()
            break

        # Receive MQTT topic in POST query param
        parameters = qs_parse(req.split(" ")[1])
        if len(parameters) > 0 and parameters["topic"] != None:
            topic_pub = parameters["topic"]

        l = 0
        while True:
            h = conn.readline()
            if not h or h == b'\r\n':
                break
            if 'Content-Length: ' in h:
                try:
                    l = int(h[16:-2])
                    print('Content Length is : ', l)
                except:
                    continue

        if l == 0:
            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send("Received file was empty")
            conn.close()
        else:
            postquery = conn.read(l)

            print(postquery)

            # Cancel previous script and disconnect MQTT client
            try:

                import script
                script.cancel()
                print("AFTER CANCEL")
                if mqtt_client != None:
                    mqtt_client.disconnect()
                print("AFTER DISCONNECT")
                os.remove("script.py")
                print("AFTER REMOVE")
                del sys.modules['script']
                print("AFTER CANCEL")

            except Exception as e:
                print("whoops")
                print(e)
            
            f = open("script.py", "w")
            f.write(postquery)
            f.close()

            print("File written!")

            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send("File saved")
            conn.close()

            # Setup MQTT Client
            mqtt_client = mqtt.start(mqtt_server, client_id)

            import script
            script_result = script.exec(mqtt_client)

