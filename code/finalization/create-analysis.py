#!/usr/bin/env python3

import json
import logging
import pathlib
import sys
from collections import defaultdict
import re
from functools import reduce
from math import floor, log

import click
import os
import csv

import numpy as np
import pandas as pd

CSV_COLUMNS = ['level', 'trafficEmulation', 'kem', 'sig',
               *reduce(lambda x,y: x+y, [ [ f'{part}Median', f'{part}Avg'] for part in [ 'partA', 'partB', 'partAll' ]]),
               'segments', 'packetsClient', 'packetsServer', 'handshakeServerPushes', 'connections', 'clientServerBytes', 'serverClientBytes']

"""Security Levels as defined by NIST"""
levels = {
    'p256_kyber512': 1,
    'kyber1024': 5,
    'p384_bikel3': 3,
    'p384_kyber768': 3,
    'bikel1': 1,
    'kyber90s1024': 5,
    'secp384r1': 3,
    'hqc256': 5,
    'kyber90s512': 1,
    'bikel3': 3,
    'kyber768': 3,
    'hqc192': 3,
    'p384_hqc192': 3,
    'p521_kyber1024': 5,
    'X25519': 1,
    'p256_bikel1': 1,
    'p521_hqc256': 5,
    'kyber90s768': 3,
    'p256_hqc128': 1,
    'kyber512': 1,
    'secp521r1': 5,
    'prime256v1': 1,
    'hqc128': 1,
}

sig_levels = {
    'dilithium2': 2,
    'dilithium2_aes': 2,
    'dilithium3': 3,
    'dilithium3_aes': 3,
    'dilithium5': 5,
    'dilithium5_aes': 5,
    'falcon1024': 5,
    'falcon512': 1,
    'p256_dilithium2': 2,
    'p256_falcon512': 1,
    'p256_sphincssha256128frobust': 1,
    'p256_sphincsharaka128fsimple': 1,
    'p384_dilithium3': 3,
    'p521_dilithium5': 5,
    'p521_falcon1024': 5,
    'rsa3072_dilithium2': 2,
    'rsa:1024': 0,
    'rsa:2048': 0,
    'rsa:3072': 1,
    'rsa:4096': 1,
    'sphincsharaka128frobust': 1,
    'sphincsharaka128fsimple': 1,
    'sphincsharaka128srobust': 1,
    'sphincsharaka128ssimple': 1,
    'sphincsharaka192frobust': 3,
    'sphincsharaka192fsimple': 3,
    'p384_sphincsharaka192fsimple': 3,
    'sphincsharaka192srobust': 3,
    'sphincsharaka192ssimple': 3,
    'sphincsharaka256frobust': 5,
    'sphincsharaka256fsimple': 5,
    'p521_sphincsharaka256fsimple': 5,
    'sphincsharaka256srobust': 5,
    'sphincsharaka256ssimple': 5,
    'sphincssha256128frobust': 1,
    'sphincssha256128fsimple': 1,
    'sphincssha256128srobust': 1,
    'sphincssha256128ssimple': 1,
    'sphincssha256192frobust': 3,
    'sphincssha256192fsimple': 3,
    'sphincssha256192srobust': 3,
    'sphincssha256192ssimple': 3,
    'sphincssha256256frobust': 5,
    'sphincssha256256fsimple': 5,
    'sphincssha256256srobust': 5,
    'sphincssha256256ssimple': 5,
    'sphincsshake256128frobust': 1,
    'sphincsshake256128fsimple': 1,
    'sphincsshake256128srobust': 1,
    'sphincsshake256128ssimple': 1,
    'sphincsshake256192frobust': 3,
    'sphincsshake256192fsimple': 3,
    'sphincsshake256192srobust': 3,
    'sphincsshake256192ssimple': 3,
    'sphincsshake256256frobust': 5,
    'sphincsshake256256fsimple': 5,
    'sphincsshake256256srobust': 5,
    'sphincsshake256256ssimple': 5,
}

def human_format(number):
    if number == 0:
        return ''
    if number < 1000:
        return str(number)
    units = ['', 'k', 'M', 'G', 'T', 'P']
    k = 1000.0
    magnitude = int(floor(log(number, k)))
    return '%.1f%s' % (number / k**magnitude, units[magnitude])


@click.command()
@click.argument('result_dir', required=True, type=click.Path(exists=True, dir_okay=True, file_okay=False))
def analyse(result_dir: pathlib.Path):
    logging.basicConfig(level=logging.INFO)
    result_dir = pathlib.Path(result_dir)
    output_writer = csv.DictWriter(sys.stdout, CSV_COLUMNS, lineterminator='\n')

    logging.info(f'Start processing {result_dir}')
    analyze_dir(result_dir, output_writer)


def extract_run(file_name: str):
    m = re.search(r'.*run(\d+).*', file_name)
    if m is None:
        raise Exception(f'Could not extract run from {file_name}.')
    return m.group(1)


def analyze_dir(result_dir: pathlib.Path, output_writer: csv.DictWriter):
    results = defaultdict(lambda: dict())
    result_name = os.path.basename(result_dir)
    full_sphincs = False

    for file_name in os.listdir(result_dir):
        result_file = result_dir / file_name

        if file_name == 'client_results.csv' or file_name == 'loadgen_results.csv':
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    run = entry.get('run')
                    raw_run_vars: str = entry.get('run_vars')
                    run_vars = json.loads(raw_run_vars.replace("'", '"'))
                    kem = run_vars.get('kem_alg')
                    results[run]['kem'] = kem.replace('_', '\\_')
                    sig = run_vars.get('sig_alg')
                    results[run]['sig'] = sig.replace('_', '\\_')
                    if 'sphincssha' in sig:
                        full_sphincs = True

                    if run_vars.get('tc') is not None:
                        results[run]['trafficEmulation'] = run_vars.get('tc')

                    if result_name == 'kem' or 'kem' in result_name:
                        level = levels[kem]
                    elif result_name == 'sig' or 'sig' in result_name:
                        level = sig_levels[sig]
                    else:
                        level = max(levels[kem], sig_levels[sig])

                    if '_' in kem or '_' in sig:
                        level += 0.5

                    results[run]['level'] = level

                    if entry['connections'] != '':
                        results[run]['connections'] = int(entry['connections'])
                    else:
                        results[run]['connections'] = 0

        elif re.match(r'run\d*\.csv\.median', file_name):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['packetsClient'] = int(float(entry['handshake_c_packets']))
                    results[run]['packetsServer'] = int(float(entry['handshake_s_packets']))
                    if 'handshake_c_bytes' in entry:
                        results[run]['clientServerBytes'] = int(float(entry['handshake_c_bytes']))
                    if 'handshake_s_bytes' in entry:
                        results[run]['serverClientBytes'] = int(float(entry['handshake_s_bytes']))
                    if 'handshake_s_tcp_pushs' in entry:
                        results[run]['handshakeServerPushes'] = int(float(entry['handshake_s_tcp_pushs']))

        elif file_name.endswith('tcp-segments.csv'):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['segments'] = entry['packets']

        elif file_name.endswith('client_hello_change_cipher.median.csv'):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['partAllMedian'] = int(float(entry['latency_median']))

        elif file_name.endswith('client_hello_change_cipher.avg.csv'):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['partAllAvg'] = float(entry['latency_avg'])

        elif file_name.endswith('client_server_hello.median.csv'):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['partAMedian'] = int(float(entry['latency_median']))

        elif file_name.endswith('client_server_hello.avg.csv'):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['partAAvg'] = float(entry['latency_avg'])

        elif file_name.endswith('server_hello_change_cipher.median.csv'):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['partBMedian'] = int(float(entry['latency_median']))

        elif file_name.endswith('server_hello_change_cipher.avg.csv'):
            run = extract_run(file_name)
            with open(result_file) as r_f:
                reader = csv.DictReader(r_f)
                for entry in reader:
                    results[run]['partBAvg'] = float(entry['latency_avg'])

        else:
            logging.debug(f'Unknown file {result_file}')

    output = results.values()
    output = sorted(output, key=lambda x: (x.get('level'), x.get('kem'), x.get('sig')))

    for run in output:
        run['level'] = int(float(run['level']))

        if 'level1' in result_name and 1 <= run['level'] <=2:
            run['level'] = 1

        kem = run['kem']
        if kem == 'secp384r1':
            run['kem'] = 'p384'
        elif kem == 'secp521r1':
            run['kem'] = 'p521'
        elif kem == 'prime256v1':
            run['kem'] = 'p256'
        sig: str = run['sig']

        if not full_sphincs and 'sphincsharaka' in sig:
            sig = sig.replace('haraka', '').replace('fsimple', '')
            run['sig'] = sig

        for part in ['A', 'B', 'All']:
            for part_name in ['Median', 'Avg']:
                entry_name = f'part{part}{part_name}'
                if entry_name in run:
                    part_ms = run[entry_name] / 1000000
                    run[entry_name] = part_ms
                else:
                    logging.error(f'No {entry_name} in run')

        if run.get('connections'):
            run['connections'] = human_format(run.get('connections'))

    output_writer.writeheader()
    output_writer.writerows(output)


if __name__ == '__main__':
    analyse()
