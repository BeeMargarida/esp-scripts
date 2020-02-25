# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import uos, machine
#uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
#import webrepl
#webrepl.start()
gc.collect()

##############################

import wifi
import server
import mqtt

mqtt_server = '192.168.1.179:1883'
client_id = ubinascii.hexlify(machine.unique_id())
topic_pub = b'results'

wifi.connect()
mqtt_client = mqtt.start()
server.start(mqtt_client, topic_pub)