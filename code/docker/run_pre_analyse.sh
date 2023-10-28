#!/usr/bin/env bash

[[ -z "$HOST_DIR" ]] && echo "Need to set HOST_DIR" && exit 1;
[[ -z "$OUT_DIR" ]] && echo "Need to set OUT_DIR" && exit 1;
[[ -z "$CPU_PROFILING" ]] && echo "Need to set CPU_PROFILING" && exit 1;

COMPOSE_FILE=docker-compose.yml

echo "Building docker images..."
docker --log-level ERROR compose -f $COMPOSE_FILE build --quiet pre-analyzer

# Start Pre Analyse
docker --log-level ERROR compose -f $COMPOSE_FILE up --exit-code-from pre-analyzer pre-analyzer
e=$?
docker --log-level ERROR compose -f $COMPOSE_FILE logs pre-analyzer > $OUT_DIR/docker.log

# Cleanup containers
docker --log-level ERROR compose -f $COMPOSE_FILE down pre-analyzer

exit $e
