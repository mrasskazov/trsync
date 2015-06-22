#!/bin/bash -ex

export DST=${HOME:-.}/repos

if [ -z $1 ]; then
    echo "Using: $0 <mirror_name>"
    exit 1
else
    export MIRROR_NAME=$1
fi

if [ ! -d ${DST} ]; then
    mkdir -p ${DST}/files
fi

bash -x mirrors/mirror_update.sh mos-${MIRROR_NAME}
[ ! -L repos/${MIRROR_NAME} ] && ln -s -T files/mos-${MIRROR_NAME}-latest repos/${MIRROR_NAME} || true
