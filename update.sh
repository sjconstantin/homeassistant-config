#!/bin/sh
docker pull homeassistant/home-assistant
docker stop HomeAssistant
docker rm HomeAssistant
docker run --name HomeAssistant --restart=always --net=host -itd -v /volume1/main/Docker/HomeAssistant/config:/config -v /etc/localtime:/etc/localtime:ro -v /usr/syno/etc/certificate/system/default:/cert homeassistant/home-assistant
