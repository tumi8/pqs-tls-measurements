# PQC TLS Measurements

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10054882.svg)](https://doi.org/10.5281/zenodo.10054882)

This repository containes the published measurement and evaluation scripts for the paper *The Performance of Post-Quantum TLS 1.3*, by Markus Sosnowski, Florian Wiedner, Eric Hauser, Lion Steger, Dimitrios Schoinianakis, Sebastian Gallenmüller, and Georg Carle.
The paper was published at [CoNEXT 2023](https://conferences.sigcomm.org/co-next/2023/#!/home) and can be accessed under [DOI:10.1145/3624354.3630585](https://doi.org/10.1145/3624354.3630585).

If you could find our work useful, consider citing our paper. 
You can use:

```bibtex
@inproceedings{SosnowskiPQTLS23,
  title = {{The Performance of Post-Quantum TLS 1.3}},
  author = {Sosnowski, Markus and Wiedner, Florian and Hauser, Eric and Steger, Lion and Schoinianakis, Dimitrios and Gallenm{\"u}ller, Sebastian and Carle, Georg},
  booktitle = {Proceedings of the International Conference on emerging Networking EXperiments and Technologies (CoNEXT '23)},
  year = 2023,
  address = {Paris, France},
  month = dec,
  keywords = {performance measurements, post-quantum cryptography},
  homepage = {https://tumi8.github.io/pqs-tls-measurements},
  doi = {10.1145/3624354.3630585},
}

```


## PQC TLS Measurements and Evaluations

Our measurements were originally conducted in an raw hardware with an optical splitter setup.
Details can be found under https://tumi8.github.io/pqs-tls-measurements
For the sake of reproducibility, we adapted our setup to run in an docker environment.

Requirements:
* Linux (ideally, `debian bullseye`)
* Installed Docker (https://docs.docker.com/engine/install/debian/), we tested it with version 24.0.6
* Python3 `apt-get install python3`
* Python3 Libraries: `apt-get install python3-click python3-yaml`

To run our (dockerized) PQC TLS measurements:

```bash
./experiment.py --output-dir $RESULTS all-kem all-sig
```

We pre-defined the following experiments:

* all-kem
    * Evaluate all Key Agreements (KA) together with rsa:2048 as Signature Algorithm (SA)
* all-sig
    * Evaluate all SA together with X25519 as KA
* all-[kem|sig]-scenarios
  * same as all-kem and all-sig but with the emulated constrained environments
* level[1,2,3]
  * Every possible combination of SA and KA on the respective levels (we grouped level one and two together)

Our evaluations can be run with the `evaluate.py` script

```bash
./evaluate.py --output-dir $EVAL_OUTPUT $RESULTS/*
```

To reproduce the measurements from our paper, run each experiment (storing the results under `$RESULTS`). Then, run the evaluation script:

```bash
./experiment.py --output-dir $RESULTS all-kem all-sig all-kem-scenarios all-sig-scenarios level1 level3 level5
./evaluate.py --output-dir $EVAL_OUTPUT $RESULTS/*
```

You can also download the pcaps we captured on our hardware setup and evaluate them with the scripts. Note that you need the docker hosts needs Linux Kernel 5.9 (e.g., from `debian bullseye`) to analyze the cpu profilings. 

```bash
rsync rsync://m1725057@dataserv.ub.tum.de/m1725057/ $RAW_RESULTS/
./evaluate.py --output-dir $EVAL_OUTPUT $RAW_RESULTS/*
```

### Specialized Analyses

The evaluation script can be paramtereized with `--cpu-profiling True` and `--deviation-analysis True`. The former makes only sense if the CPU usage was monitored with `perf` (we published perf results, however, the docker scripts are unable to generate them), the latter makes only sense for the `level*` experiments.
