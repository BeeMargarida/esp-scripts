import usocket as socket
import ujson

async def log_to_logstash(data):
    print('Sending data to Logstash. Data:', data)
    try:
        addr = socket.getaddrinfo("192.168.1.199", 5959)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send(ujson.dumps(data))
        s.close()
    except OSError as e:
        print('Error sending data to Logstash:', e)