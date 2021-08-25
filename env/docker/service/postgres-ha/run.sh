#!/bin/bash

mkdir -p /data/postgres/{master,slave}

# set config
docker config create postgresql_config postgresql.conf

# set secret
echo 'youngha' | docker secret create postgresql_password -

# run
docker stack deploy --compose-file=docker-compose.yml postgres --with-registry-auth
