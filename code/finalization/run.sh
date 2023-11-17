#!/usr/bin/env bash

set -e
set -x

out_name=/out
/opt/create-analysis.py /srv > $out_name/latencies.csv
/opt/create-recommendation-plot.py $out_name/latencies.csv $out_name


if [[ $DEVIATION_ANALYSIS == "True" ]]; then
    /opt/derivation-analysis.py $out_name/latencies.csv > $out_name/deviations.csv
    /opt/create-deviation-plot.py $out_name/derivations.csv $out_name/deviations
fi

if [[ "$CPU_PROFILING" == "True" ]]; then
  /opt/eval_profiling.py /srv $out_name/profiling.csv
fi
