#!/bin/bash

set -e
set -x

# define variables
# Set KEM to one defined in https://github.com/open-quantum-safe/openssl#key-exchange
# ENV variables
[[ -z "$KEM_ALG" ]] && echo "Need to set KEM_ALG" && exit 1;
[[ -z "$SIG_ALG" ]] && echo "Need to set SIG_ALG" && exit 1;
[[ -z "$MEASUREMENT_TIME" ]] && echo "Need to set MEASUREMENT_TIME" && exit 1;

if [[ ! -z "$NETEM_TC" ]]; then
  PORT=eth0
  eval "tc qdisc add dev $PORT root netem $NETEM_TC"
fi

SERVER_IP="$(dig +short server)"

DATETIME=$(date +"%F_%T")

CA_DIR="/opt/shared"

cd "$OPENSSL_PATH" || exit

echo "Running $0 with SIG_ALG=$SIG_ALG and KEM_ALG=$KEM_ALG"

if [ "$CPU_PROFILING" = "True" ]; then
  echo "Will export cpu profiling"
  FG_FREQUENCY=96
  bash -c "perf record -o /out/perf-client.data -F ${FG_FREQUENCY} -C 1 -g" &
  PERF_PID=$!
fi

bash -c "tcpdump -w /out/latencies-post_run${RUN}.pcap src host $SERVER_IP and src port 4433" &
TCPDUMP_PID=$!

echo "{\"tc\": \"$NETEM_TC\", \"kem_alg\": \"$KEM_ALG\", \"sig_alg\": \"$SIG_ALG\"}" > "/out/${DATETIME}_client_run${RUN}.loop"

sleep 5

# Run handshakes for $TEST_TIME seconds
bash -c "taskset -c 1 ${OPENSSL} s_time -curves $KEM_ALG  -connect $SERVER_IP:4433 -new -time $MEASUREMENT_TIME -verify 1 -www '/' -CAfile $CA_DIR/CA.crt > /out/opensslclient_run${RUN}.stdout 2> /out/opensslclient_run${RUN}.stderr"

if [ "$CPU_PROFILING" = "True" ]
then
    kill $PERF_PID
fi

sleep 30  # Make sure it is finished and written out

kill -2 $TCPDUMP_PID

if [ "$CPU_PROFILING" = "True" ]
then
    perf archive /out/perf-client.data
    echo "CPU profiling data can be found at /out/perf-client.data"
fi

echo "client finished sending $(date), results can be found at /out/results-openssl-$KEM_ALG-$SIG_ALG.txt"
