#!/usr/bin/env bash

[[ -z "$KEM_ALG" ]] && echo "Need to set KEM_ALG" && exit 1;
[[ -z "$SIG_ALG" ]] && echo "Need to set SIG_ALG" && exit 1;
[[ -z "$RUN" ]] && echo "Need to set RUN" && exit 1;
[[ -z "$HOST_DIR" ]] && echo "Need to set HOST_DIR" && exit 1;

COMPOSE_FILE=docker-compose.yml

echo "Building docker images..."
docker --log-level ERROR compose -f $COMPOSE_FILE build --quiet

# Start Test Server detached
docker --log-level ERROR compose -f $COMPOSE_FILE up -d server

# Wait until server has started
until docker --log-level ERROR compose -f $COMPOSE_FILE logs server | grep -q "ACCEPT";
do
  sleep 1;
done

# Run client until it has finished
docker --log-level ERROR compose -f $COMPOSE_FILE up --exit-code-from client client
e=$?

# Save client log
docker --log-level ERROR compose -f $COMPOSE_FILE logs client > $HOST_DIR/client/run${RUN}.log

# Now we can kill the server
docker --log-level ERROR compose -f $COMPOSE_FILE stop server

# Save server logs
docker --log-level ERROR compose -f $COMPOSE_FILE logs server > $HOST_DIR/server/run${RUN}.log

# Compress pcaps and move them to the timestamper directory
docker --log-level ERROR compose -f $COMPOSE_FILE up post-processor

# Cleanup containers
docker --log-level ERROR compose -f $COMPOSE_FILE down --volumes

exit $e
