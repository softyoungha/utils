#!/bin/bash

docker swarm init --advertise-addr "$(hostname -I | awk '{ print $1 }'):2377" | \
  awk '/docker swarm join --token /' | \
  sed -e 's/^[[:space:]]*//' > \
  ~/swarm_token