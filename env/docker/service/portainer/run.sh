#!/bin/bash

# 모든 서버에서 해당 커맨드 실행
mkdir -p /data/portainer

# run
docker stack deploy --compose-file=docker-compose.yml portainer --with-registry-auth