#!/bin/sh

VERSION=latest

docker pull homeassistant/home-assistant:$VERSION
docker rm -f HomeAssistant
docker run --name HomeAssistant --restart=always --net=host -d \
  -v /volume1/main/Docker/HomeAssistant/config:/config \
  -v /etc/localtime:/etc/localtime:ro \
  -v /usr/syno/etc/certificate/system/default:/cert \
  homeassistant/home-assistant:$VERSION

docker image prune -f

#docker pull homeassistant/home-assistant:2025.12.0
#docker stop HomeAssistant
#docker rm HomeAssistant
#docker run --name HomeAssistant --restart=always --net=host -itd -v /volume1/main/Docker/HomeAssistant/config:/config -v /etc/localtime:/etc/localtime:ro #-v /usr/syno/etc/certificate/system/default:/cert homeassistant/home-assistant:2025.12.0
#docker image prune -f
