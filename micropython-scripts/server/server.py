import socket
from machine import Pin
from mqtt_library import MQTTClient

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


def start(mqtt_client, topic_pub):
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
            f = open("script.py", "w")
            f.write(postquery)
            f.close()

            print("File written!")

            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send("File saved")
            conn.close()

            import script
            script_result = script.exec(mqtt_client)

            # Publish script result in MQTT topic
            # mqtt_client.publish(topic_pub, '%s' % script_result)

