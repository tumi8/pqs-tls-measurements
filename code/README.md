# PQC TLS Measurements

These measurements were originally conducted in an raw hardware with an optical splitter setup.
Details can be found under https://tumi8.github.io/pqs-tls-measurements
For the sake of reproducibility we adapted our setup to run under docker.

Requirements:
* Installed Docker (https://docs.docker.com/engine/install/debian/)
* Python3 `apt-get install python3`
* Python3 Libraries: `apt-get install python3-click python3-yaml`

To run our (dockerized) PQC TLS measurements:

    ./experiment.py --output-dir /opt/experiments all-kem all-sig

We pre-defined the following experiments:

* all-kem
    * Evaluate all Key Agreements (KA) together with rsa:2048 as Signature Algorithm (SA)
* all-sig
    * Evaluate all SA together with rsa:2048 as KA
* all-[kem|sig]-scenarios
  * same as all-kem and all-sig but with the emulated constrained environments
* level[1,2,3]
  * Every possible combination of SA and KA on the respective levels (we grouped level one and two together)

Our evaluations can be run with the `evaluate.py` script

    ./evaluate.py --output-dir /opt/pqc-analysis /opt/experiments/*

To reproduce all measurements from our paper and save the raw results under `$RAW_RESULTS` and the evaluations under `$EVAL_OUTPUT`:

    ./experiment.py --output-dir $RAW_RESULTS all-kem all-sig all-kem-scenarios all-sig-scenarios level1 level3 level5
    ./evaluate.py --output-dir $EVAL_OUTPUT $RAW_RESULTS/*

