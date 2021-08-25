#!/bin/bash

# 모든 서버에서 해당 커맨드 실행
mkdir -m 777 -p /data/minio/{1,2,3,4}-{1,2}

# network
docker network create --attachable --driver overlay --subnet 192.168.10.0/24 minio_net

# set nginx conf
docker config create minio_nginx_conf nginx.conf

# set secrets
echo 'youngha' | docker secret create access_key -
echo 'youngha' | docker secret create secret_key -

# run
docker stack deploy --compose-file=docker-compose.yml minio --with-registry-auth