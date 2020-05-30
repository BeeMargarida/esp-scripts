FROM ubuntu:16.04

# Setup influxDB

# RUN apt install apt-transport-https curl -y

# RUN curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -

# RUN echo "deb https://repos.influxdata.com/ubuntu/ xenial stable" | sudo tee /etc/apt/sources.list.d/influxdb.list

# RUN apt update && sudo apt install influxdb

# RUN sudo systemctl start influxdb

# Setup integration mqtt with influxDB

RUN apt-get update && apt-get -y install python3 python3-pip

RUN pip3 install --upgrade mqtt2influxdb

RUN mkdir /etc/bigclown

COPY ./mqtt2influxdb.yml /etc/bigclown/mqtt2influxdb.yml

RUN mqtt2influxdb -c /etc/bigclown/mqtt2influxdb.yml --test

# RUN pm2 start `which python3` --name "mqtt2influxdb" -- `which mqtt2influxdb` -c /etc/bigclown/mqtt2influxdb.yml

# RUN pm2 save