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

def run_analysis(input_dir, output_dir, profiling: bool, cmd: str, experiment: str, deviation_analysis: bool):
    success_file = output_dir / '_SUCCESS'
    if output_dir.exists():
        if success_file.exists():
            logging.info(f'{output_dir} already present, skipping')
            return
        raise click.ClickException(f'Output Directory {output_dir} already exists, please set new directory')
    output_dir.mkdir(parents=True)
    subprocess_env = os.environ.copy()
    subprocess_env['CPU_PROFILING'] = 'True' if profiling else 'False'
    subprocess_env['DEVIATION_ANALYSIS'] = 'True' if deviation_analysis else 'False'
    subprocess_env['HOST_DIR'] = str(input_dir)
    subprocess_env['OUT_DIR'] = str(output_dir)
    subprocess_env['EXPERIMENT'] = experiment
    run_cmd = script_dir / 'docker' / cmd
    subprocess.run(run_cmd, text=True, env=subprocess_env)
    success_file.touch()


@click.command()
@click.option('-o', '--output-dir', required=True, type=click.Path(file_okay=False, dir_okay=True))
@click.option('-f', '--cpu-profiling', type=bool)
@click.option('-d', '--deviation-analysis', type=bool)
@click.argument('input-dirs', nargs=-1, required=True, type=click.Path(file_okay=False, dir_okay=True, exists=True))
def main(input_dirs: List[str], output_dir: str, cpu_profiling: bool, deviation_analysis: bool):
    output_dir = pathlib.Path(output_dir)
    input_dirs = [pathlib.Path(input_dir) for input_dir in input_dirs]
    logging.basicConfig(level=logging.INFO)
    for input_dir in input_dirs:
        experiment = os.path.basename(input_dir)
        logging.info(f'Starting Pre-Analyse of {experiment}')
        run_analysis(input_dir, output_dir / experiment, cpu_profiling, 'run_pre_analyse.sh', experiment, deviation_analysis)
        logging.info(f'Starting Final-Analyse of {experiment}')
        run_analysis(output_dir / experiment, output_dir / f'{experiment}-final', False, 'run_final_analyse.sh', experiment, deviation_analysis)


if __name__ == '__main__':
    main()
