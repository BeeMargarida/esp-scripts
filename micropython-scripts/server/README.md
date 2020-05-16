# ESP micropython server

## Setup

These instructions will send the code to the ESP:

1. Make virtualenv with `virtualenv .`
2. Activvate virtualenv with `source bin/activate`
3. Install `adafruit-ampy` with `pip3 install adafruit-ampy`
4. With ampy, copy scripts with:
    * `ampy --port /dev/ttyUSB0 --baud 115200 put wifi.py`
    * `ampy --port /dev/ttyUSB0 --baud 115200 put server.py`
    * `ampy --port /dev/ttyUSB0 --baud 115200 put boot.py`
5. Access terminal with `picocom /dev/ttyUSB0`
6. Reset ESP32
7. See if it doesn't break

The ESP's IP is presented in the `picocom` console.


### Commands

* ampy --port /dev/ttyUSB0 --baud 115200 put <script> 

* picocom /dev/ttyUSB0 --baud 115200
