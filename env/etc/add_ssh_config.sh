#!/bin/bash
# ssh profile 생성

mkdir -p ${HOME}/.ssh


if [[ -f "${HOME}/.ssh/config" ]]; then
    sudo chmod 777 "${HOME}/.ssh/config"
fi

/bin/cat <<EOM >"${HOME}/.ssh/config"
# dev
Host server-dev-1
    HostName 10.0.0.1
    User youngha
    StrictHostKeyChecking no

Host server-dev-2
    HostName 10.0.0.2
    User youngha
    StrictHostKeyChecking no

# prd
Host server-prd-1
    HostName 10.0.1.1
    User youngha
    StrictHostKeyChecking no

Host server-prd-2
    HostName 10.0.1.2
    User youngha
    StrictHostKeyChecking no

EOM

chmod 400 "${HOME}/.ssh/config"