#!/bin/bash

mkdir -p /data/mysql/{master,slave}

# set config
docker config create mysql_config my.cnf

# set secret
echo 'youngha' | docker secret create mysql_password -

# run
docker stack deploy --compose-file=docker-compose.yml mysql --with-registry-auth
