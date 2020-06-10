#!/bin/bash

mkdir ./firmware-32

cd ~/Documents/micropython

# make -C ports/esp8266 submodules
# make -C mpy-cross

cd ./ports/esp32

make submodules

rm -rf ./build-GENERIC

cp -R ~/Documents/esp-scripts/scripts/* ./modules/

rm -rf ./modules/boot.py

for i in {15..19..1}
    do
        cp ~/Documents/esp-scripts/firmware-scripts/$i/boot.py ./modules/boot.py 
        make 
        cp ./build-GENERIC/firmware.bin ~/Documents/esp-scripts/firmware-32/firmware-$i.bin
    done