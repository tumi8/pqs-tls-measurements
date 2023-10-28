#!/bin/bash
DEFAULT_BUCKET_SIZE=100   # default bucket size of the histogram
DEFAULT_TRIM_MS=1000         # default cut the first TRIM_MS ms from evaluation

if [ "$BUCKET_SIZE" = '' ]; then
	BUCKET_SIZE=$DEFAULT_BUCKET_SIZE
fi

if [ "$TRIM_MS" = '' ]; then
	TRIM_MS=$DEFAULT_TRIM_MS
fi

BASENAME="$(readlink -f "$0")"
BASEDIR="$(dirname "$BASENAME")"
BASENAME="$(basename "$BASENAME")"

PYTHON=$HOME/.venv/bin/python3

[[ -x "$PYTHON" ]] || PYTHON=python3


log () {
	printf "%s\n" "$*" >&2
}

err() {
	log "$*"
	exit 2
}

help() {
	err usage: "$BASENAME" capturename
}

analysis() {
	local name="$1"

	[[ -e "$name" ]] && name="$(realpath "$name")"

	local bname="$(basename "$name")"

	# histogram
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "bucket_size=$BUCKET_SIZE" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/client_server_hello/latency-hist.sql" > "${bname}.bucket_size$BUCKET_SIZE.trim_ms$TRIM_MS.client_server_hello.hist.csv"
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "bucket_size=$BUCKET_SIZE" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/client_hello_change_cipher/latency-hist.sql" > "${bname}.bucket_size$BUCKET_SIZE.trim_ms$TRIM_MS.client_hello_change_cipher.hist.csv"
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "bucket_size=$BUCKET_SIZE" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/server_hello_change_cipher/latency-hist.sql" > "${bname}.bucket_size$BUCKET_SIZE.trim_ms$TRIM_MS.server_hello_change_cipher.hist.csv"

	# Get TCP Segments in handshake
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/dump-tcp-segments.sql" > "${bname}.trim_ms$TRIM_MS.dump-tcp-segments.csv"

  # Get median latency
  psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/client_server_hello/latency-median.sql" > "${bname}.trim_ms$TRIM_MS.client_server_hello.median.csv"
  psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/client_hello_change_cipher/latency-median.sql" > "${bname}.trim_ms$TRIM_MS.client_hello_change_cipher.median.csv"
  psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/server_hello_change_cipher/latency-median.sql" > "${bname}.trim_ms$TRIM_MS.server_hello_change_cipher.median.csv"
  
  # Get average latency
  psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/client_server_hello/latency-avg.sql" > "${bname}.trim_ms$TRIM_MS.client_server_hello.avg.csv"
  psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/client_hello_change_cipher/latency-avg.sql" > "${bname}.trim_ms$TRIM_MS.client_hello_change_cipher.avg.csv"
  psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/server_hello_change_cipher/latency-avg.sql" > "${bname}.trim_ms$TRIM_MS.server_hello_change_cipher.avg.csv"
}

test $# -lt 1 && help

analysis "$@"
