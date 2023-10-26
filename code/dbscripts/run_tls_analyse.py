#!/usr/bin/env python3
import multiprocessing
import os
import re
import subprocess

import pandas as pd

import click


@click.command()
@click.argument('from-dir', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.argument('to-dir', type=click.Path(file_okay=False, dir_okay=True))
def main(from_dir, to_dir):
    files = os.listdir(from_dir)
    os.makedirs(to_dir, exist_ok=True)

    with multiprocessing.Pool() as p:
        p.starmap(process_file, [(f, from_dir, to_dir) for f in files])

    for file in os.listdir(to_dir):
        file_path = os.path.join(to_dir, file)
        if re.match(r'run\d{1,8}.csv', file):
            pdf = pd.read_csv(file_path)
            pdf = pdf.dropna()
            if len(pdf.index) > 0:
                pdf.mean().to_frame().T.astype('int').to_csv(os.path.join(to_dir, f'{file}.avg'), index=False)
                pdf.sum().to_frame().T.astype('int').to_csv(os.path.join(to_dir, f'{file}.sum'), index=False)
                pdf.median().to_frame().T.astype('int').to_csv(os.path.join(to_dir, f'{file}.median'), index=False)

            subprocess.check_output(f'zstd --rm {file_path}', shell=True)


def process_file(file: str, from_dir: str, to_dir: str):
    file_path = os.path.join(from_dir, file)
    m = re.match(r'latencies-pre_(run\d{1,8})\.pcap\.zst', file)
    file2 = file.replace('pre', 'post')
    file2_path = os.path.join(from_dir, file2)
    if m:
        run = m.group(1)
        file_uncomressed = file_path.replace('.zst', '')
        file2_uncomressed = file2_path.replace('.zst', '')
        if '.zst' in file:
            subprocess.check_output(f'zstd -d -f {file_path} {file2_path}', shell=True)

        subprocess.check_output(f'~/experiment-script/dbscripts/tls_handshakes.py {file_uncomressed} {file2_uncomressed} > {os.path.join(to_dir, run)}.csv', shell=True)

        os.remove(file_uncomressed)
        os.remove(file2_uncomressed)

if __name__ == "__main__":
    main()
