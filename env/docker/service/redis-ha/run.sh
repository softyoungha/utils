#!/bin/bash

mkdir -p /data/redis/{master,slave}

# set config
docker config create mysql_config my.cnf

# set secret
echo 'youngha' | docker secret create redis_password -

# run
docker stack deploy --compose-file=docker-compose.yml redis --with-registry-auth
