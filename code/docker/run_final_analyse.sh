#!/usr/bin/env bash

[[ -z "$HOST_DIR" ]] && echo "Need to set HOST_DIR" && exit 1;
[[ -z "$OUT_DIR" ]] && echo "Need to set OUT_DIR" && exit 1;
[[ -z "$CPU_PROFILING" ]] && echo "Need to set CPU_PROFILING" && exit 1;

COMPOSE_FILE=docker-compose.yml

echo "Building docker images..."
docker --log-level ERROR compose -f $COMPOSE_FILE build --quiet final-analyzer

# Start Analyze
docker --log-level ERROR compose -f $COMPOSE_FILE up --exit-code-from final-analyzer final-analyzer
status=$?
docker --log-level ERROR compose -f $COMPOSE_FILE logs final-analyzer > $OUT_DIR/docker.log

# Cleanup container
docker --log-level ERROR compose -f $COMPOSE_FILE down final-analyzer

exit $status
