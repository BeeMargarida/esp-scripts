import socket
from machine import Pin


def start():
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

        l = 0
        while True:
            h = conn.readline()
            if not h or h == b'\r\n':
                break
            if 'Content-Length: ' in h:
                try:
                    l = int(h[16:-2])
                    print ('Content Length is : ', l)
                except:
                    continue

        if l == 0:
            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send("Received file was empty")
            conn.close()
        else:
            postquery = conn.read(l)
            print(postquery)
            f = open("script.py", "w")
            f.write(postquery)
            f.close()
            
            import script
            script.exec()

            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send("File executed")
            conn.close()