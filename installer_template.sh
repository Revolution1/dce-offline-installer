#!/usr/bin/env bash

DOCKER_OFFLINE="{{docker}}"
DOCKER_EXT_PATH="{{docker_ext_path}}"
DCE_TAR="{{dce}}"
COMPOSE="{{compose}}"

##### install docker #####

tar -xzvf $DOCKER_OFFLINE
cd $DOCKER_EXT_PATH
/bin/sh ./install.sh
cd ..
service docker start
docker version

##### install compose #####

cp $COMPOSE /usr/bin/docker-compose
chmod 755 /usr/bin/docker-compose

##### load dce images #####

docker load < $DCE_TAR
docker images