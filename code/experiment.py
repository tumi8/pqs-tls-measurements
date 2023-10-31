#!/usr/bin/env python3
import itertools
import logging
import os
import pathlib
import subprocess
from typing import List
import yaml

import click

script_dir = pathlib.Path(__file__).parent
loop_var_options = list(map(lambda x: x.replace('.yml', ''), os.listdir(script_dir / 'loop_vars')))


def run_experiment(run, output_dir, kem: str, sig: str, tc: str):
    subprocess_env = os.environ.copy()
    subprocess_env['KEM_ALG'] = kem
    subprocess_env['SIG_ALG'] = sig
    subprocess_env['NETEM_TC'] = tc
    subprocess_env['CPU_PROFILING'] = 'False'
    subprocess_env['RUN'] = f'{run:03d}'
    subprocess_env['HOST_DIR'] = str(output_dir)
    subprocess_env['OUT_DIR'] = str(output_dir)
    run_cmd = script_dir / 'docker' / 'run_single_experiment.sh'
    subprocess.run(run_cmd, text=True, env=subprocess_env)


@click.command()
@click.option('-o', '--output-dir', required=True, type=click.Path(file_okay=False, dir_okay=True))
@click.argument('experiments', nargs=-1, required=True, type=click.Choice(loop_var_options, case_sensitive=False))
def main(experiments: List[str], output_dir: str):
    logging.basicConfig(level=logging.INFO)
    output_dir = pathlib.Path(output_dir)
    if output_dir.exists():
        raise click.ClickException('Output Directory already exists, please specify a new directory')
    output_dir.mkdir()
    for experiment in experiments:
        experiment_out_dir = output_dir / experiment
        (experiment_out_dir / 'client').mkdir(parents=True)
        (experiment_out_dir / 'server').mkdir(parents=True)
        run = 0
        logging.info(f'Starting {experiment} Experiment to {experiment_out_dir}')
        loop_vars_path = script_dir / 'loop_vars' / f'{experiment}.yml'
        loop_vars = yaml.safe_load(loop_vars_path.read_text())
        experiment_iterator = itertools.product(loop_vars['kem_alg'], loop_vars['sig_alg'], loop_vars['tc'])
        for kem, sig, tc in experiment_iterator:
            logging.info(f'running {run}. experiment with {kem} as KA, {sig} as SA, and NETEM config: {tc}')
            run_experiment(run, experiment_out_dir, kem, sig, tc)
            run += 1


if __name__ == '__main__':
    main()
