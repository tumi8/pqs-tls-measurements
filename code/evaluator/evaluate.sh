#!/bin/bash

set -x
set -e

OUT_DIR=/out

python3 /opt/csvgenerator_client.py $OUT_DIR /srv/client

echo "Start Postgres DB"

pg_ctlcluster 13 main start

echo "Process PCAPs using all cores"

env --chdir /var/lib/postgresql setpriv --init-groups --reuid postgres -- createuser -s root || true

cd $OUT_DIR
parallel -j $PARALLEL_JOBS "dropdb --if-exists root{%}; createdb root{%}; export PGDATABASE=root{%}; /opt/dbscripts/import.sh {}; /opt/dbscripts/analysis.sh {}" ::: /srv/timestamper/latencies-pre_*.pcap.zst

python3 /opt/dbscripts/run_tls_analyse.py /srv/timestamper /out

if [ "$CPU_PROFILING" = "True" ]
then

    for filename in /srv/server/perf*.data; do
        mkdir /root/.debug/
        tar xf "/srv/server/perf-server.data.tar_$(basename ${filename##*_} .data).bz2" -C ~/.debug
        OUT_NAME=$(basename $filename)
        perf report -f -i "$filename" -s dso -g none -F overhead,period,sample > $OUT_DIR/$OUT_NAME.txt
        rm -r /root/.debug/
    done

    for filename in /srv/client/perf*.data; do
        mkdir /root/.debug/
        tar xf "/srv/client/perf-client.data.tar_$(basename ${filename##*_} .data).bz2" -C ~/.debug
        OUT_NAME=$(basename $filename)
        perf report -f -i "$filename" -s dso -g none -F overhead,period,sample > $OUT_DIR/$OUT_NAME.txt
        rm -r /root/.debug/
    done
fi
