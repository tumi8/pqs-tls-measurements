#!/usr/bin/env bash

set -e
set -x

out_name=/out/$EXPERIMENT
mkdir -p $out_name
/opt/create-analysis.py /srv > $out_name/latencies.csv

if [[ $EXPERIMENT == level* ]]; then
    /opt/derivation-analysis.py $out_name/latencies.csv > $out_name/derivations.csv
fi