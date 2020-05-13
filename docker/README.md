# Docker micropython

Docker image that setups a micropython container that executes a boot script at startup.

## Setup

Download this folder or repo and in this directory run:

* `docker-compose build`
* `docker-compose up` or `docker-compose up --scale micropython=10` if you want 10 instances of the micropython instance (with `-d` if you want to run in detached mode)

This commands will run the wanted instances of microptyhon containers as well as a mosquitto broker.

The micropython container contains the needed scripts for the wanted functionalities and it starts the server automatically. If you want access to the IPs, run: 

`docker ps -q | xargs -n 1 docker inspect --format '{{ .Name }} {{range .NetworkSettings.Networks}} {{.IPAddress}}{{end}}' | sed 's#^/##';`

## Setup with Node-RED

After completing the instructions above, you may want to setup the containers with node-red. First, clone this [repo](https://github.com/S-R-MSc/margaridasilva-nodered). After the usual `npm install` you need to make a specific setup. 

Inside there you need to setup 2 things:
* Change the **devices URLs** in *packages/node_modules/@node-red/runtime/lib/nodes/config/devices.js* with the IPs from the docker containers
* Change the **MQTT Broker URL and PORT** in *packages/node_modules/@node-red/runtime/lib/nodes/config/config.js* with the IP from the docker container running the Mosquitto broker.

With all that set up, we can start Node-RED and make a flow.

### Commands 

To launch several instances run: 

`docker-compose up --scale micropython=10`

#### Aux commands

List all docker container names and IPs:

`docker ps -q | xargs -n 1 docker inspect --format '{{ .Name }} {{range .NetworkSettings.Networks}} {{.IPAddress}}{{end}}' | sed 's#^/##';`

Get ip addresses of container:

`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' docker-micropython_micropython_1`

Remove all images:

`docker rmi $(docker images -a -q)`

Stop and remove all containers:

`docker stop $(docker ps -a -q)`

`docker rm $(docker ps -a -q)`

Prune: 

`docker system prune`

Enter container bash:

`docker exec -it docker-micropython_micropython_1 bash`
