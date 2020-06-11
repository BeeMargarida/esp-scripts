#!/bin/bash

mkdir ./firmware

cd ~/Documents/micropython

# make -C ports/esp8266 submodules
# make -C mpy-cross

cd ./ports/esp8266

rm -rf ./build-GENERIC

cp -R ~/Documents/esp-scripts/scripts/* ./modules/

rm -rf ./modules/boot.py

for i in {1..20..1}
    do
        cp ~/Documents/esp-scripts/firmware-scripts/$i/boot.py ./modules/boot.py 
        make 
        cp ./build-GENERIC/firmware-combined.bin ~/Documents/esp-scripts/firmware/firmware-$i.bin
    done