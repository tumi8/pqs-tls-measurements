#!/bin/bash

set -e
set -x

# Set KEM to one defined in https://github.com/open-quantum-safe/openssl#key-exchange
[[ -z "$KEM_ALG" ]] && echo "Need to set KEM_ALG" && exit 1;
[[ -z "$SIG_ALG" ]] && echo "Need to set SIG_ALG" && exit 1;

if [[ ! -z "$NETEM_TC" ]]; then
  PORT=eth0
  eval "tc qdisc add dev $PORT root netem $NETEM_TC"
fi

SERVER_IP="$(dig +short server)"
DATETIME=$(date +"%F_%T")

CA_DIR="/opt/shared/"

cd "${OPENSSL_PATH}"/bin
# generate CA key and cert

${OPENSSL} req -x509 -new -newkey "${SIG_ALG}" -keyout CA.key -out CA.crt -nodes -subj "/CN=oqstest CA" -days 365 -config "${OPENSSL_CNF}"

cp CA.crt $CA_DIR

cp CA.crt /out/CA_run${RUN}.crt
cp CA.key /out/CA_run${RUN}.key
SERVER_CRT=/out/server_run${RUN}

# Optionally set server certificate alg to one defined in https://github.com/open-quantum-safe/openssl#authentication
# The root CA's signature alg remains as set when building the image

# generate new server CSR using pre-set CA.key & cert
${OPENSSL} req -new -newkey "${SIG_ALG}" -keyout $SERVER_CRT.key -out $SERVER_CRT.csr -nodes -subj "/CN=$IP"
# generate server cert
${OPENSSL} x509 -req -in $SERVER_CRT.csr -out $SERVER_CRT.crt -CA CA.crt -CAkey CA.key -CAcreateserial -days 365

echo "starting experiment: $(date)"

echo "Server has IP $SERVER_IP"

echo "{\"tc\": \"$NETEM_TC\", \"kem_alg\": \"$KEM_ALG\", \"sig_alg\": \"$SIG_ALG\"}" > "/out/${DATETIME}_server_run${RUN}.loop"

bash -c "tcpdump -w /out/latencies-pre_run${RUN}.pcap dst host $SERVER_IP and dst port 4433" &
TCPDUMP_PID=$!

if [ "$FLAME_GRAPH" = "True" ]
then
  echo "will save flame graphs"
  FG_FREQUENCY=96
  bash -c "perf record -o /out/perf-dut.data -F ${FG_FREQUENCY} -C 1 -g" &
  FLAME_GRAPH_PID=$!
fi

# Start a TLS1.3 test server based on OpenSSL accepting only the specified KEM_ALG
bash -c "taskset -c 1 ${OPENSSL} s_server -cert $SERVER_CRT.crt -key $SERVER_CRT.key -curves $KEM_ALG -www -tls1_3 -accept $CLIENT_IP:4433"

sleep 30

kill -2 $TCPDUMP_PID
kill $FLAME_GRAPH_PID

if [ "$FLAME_GRAPH" = "True" ]
then
    sleep 30
    perf archive /out/perf-client.data
    echo "Flame graph data can be found at /out/perf-client.data"
fi
