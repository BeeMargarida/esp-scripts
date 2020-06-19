# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
# import uos
#uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
#import webrepl
#webrepl.start()
#gc.collect()

##############################

import sys
import wifi
from server import Server

client_id = None
ip = None
capabilities = ['temperature', 'humidity', 'micropython']

addr = wifi.connect()
if(addr): ip = addr

server = Server(client_id, ip, capabilities)
