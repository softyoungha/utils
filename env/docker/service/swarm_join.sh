#!/bin/bash

# docker swarm join
$(cat ~/swarm_token)

# label-add: name
docker node update --label-add name=example "$(hostname)"

# label-add: number
docker node update --label-add number=1 "$(hostname)"