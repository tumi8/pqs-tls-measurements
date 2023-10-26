#!/usr/bin/env bash

zstd --rm -9 $1 $2

mkdir -p /srv/timestamper

mv $1.zst $2.zst /srv/timestamper/

CLIENT_DIR=$(dirname $1)

cp $CLIENT_DIR/*run${RUN}.loop /srv/timestamper/
