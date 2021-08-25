#!/bin/bash

# 모든 서버에서 해당 커맨드 실행
mkdir -p /data/portainer

# run
docker stack deploy --compose-file=docker-compose.yml portainer --with-registry-auth

# Portainer Server에서 Endpoints > Agent에 등록하여 연결 가능
# endpoint url: 71.52.3.161:9001
# public ip: 71.52.3.161 로 등록