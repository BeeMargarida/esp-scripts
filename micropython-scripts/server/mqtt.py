from mqtt_library import MQTTClient
import machine

last_message = 0
message_interval = 5
counter = 0

def sub_cb(topic, msg):
  print((topic, msg))
  if topic == b'notification' and msg == b'received':
    print('ESP received hello message')

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client


def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

def start():
    try:
        client = connect_and_subscribe()
    except OSError as e:
        restart_and_reconnect()

    return client

    # while True:
    #     try:
    #         client.check_msg()
    #         if (time.time() - last_message) > message_interval:
    #             msg = b'Hello #%d' % counter
    #             client.publish(topic_pub, msg)
    #             last_message = time.time()
    #             counter += 1
    #     except OSError as e:
    #         restart_and_reconnect()

