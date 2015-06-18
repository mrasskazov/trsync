#!/bin/bash -ex

export DST=${WORKSPACE:-.}/repos

if [ ! -d ${DST} ]; then
    mkdir -p ${DST}/files
fi

bash -x mirrors/mirror_update.sh mos-ubuntu
[ ! -L repos/ubuntu ] && ln -s -T files/mos-ubuntu-latest repos/ubuntu || true
bash -x mirrors/mirror_update.sh mos-centos-6
[ ! -L repos/centos-6 ] && ln -s -T files/mos-centos-6-latest repos/centos-6 || true
