#!/usr/bin/env python3
import math
import pathlib

import click
import pandas as pd
import numpy as np


def retrieve_sig_data(sig_algorithm_file, default_sig):
    d_sig = pd.read_csv(sig_algorithm_file, usecols=['level', 'kem', 'sig', 'partAllMedian'])
    d_sig = d_sig[d_sig['kem'] == 'X25519']

    sig_data = d_sig[d_sig['sig'] == default_sig]['partAllMedian']

    return d_sig, sig_data.iloc[0]


def retrieve_kem_data(kem_algorithm_file, default_kem):
    d_kem = pd.read_csv(kem_algorithm_file, usecols=['level', 'kem', 'sig', 'partAllMedian'])
    d_kem = d_kem[d_kem['sig'] == 'rsa:2048']
    kem_data = d_kem[d_kem['kem'] == default_kem]['partAllMedian']
    return d_kem, kem_data.iloc[0]


def retrieve_cross_data(cross_algorithm_file, default_sig, default_kem):
    d_level = pd.read_csv(cross_algorithm_file, usecols=['level', 'kem', 'sig', 'partAllMedian'])

    unqiue_kem = d_level['kem'].unique()
    unqiue_sig = d_level['sig'].unique()

    def add_unique_kem(row):
        row['num_sig'] = np.where(unqiue_sig == row['sig'])[0][0] + 1
        row['num_kem'] = np.where(unqiue_kem == row['kem'])[0][0] + 1
        return row

    return d_level.apply(lambda row: add_unique_kem(row), axis=1), float(d_level[(d_level['kem'] == default_kem) & (d_level['sig'] == default_sig)]['partAllMedian'].iloc[0])


def add_expectation(data, sig, kem, baseline):

    def add_expected_column(row):
        sig_part = sig[sig['sig'] == row['sig']]['partAllMedian']
        kem_part = kem[kem['kem'] == row['kem']]['partAllMedian']
        row['expected'] = float(sig_part.iloc[0]) + float(kem_part.iloc[0]) - baseline
        row['variance'] = np.round(row['expected'] - row['partAllMedian'], decimals=6)
        row['percent'] = round(row['variance']/row['expected'] * 100)
        return row

    data['expected'] = 0
    return data.apply(lambda row: add_expected_column(row), axis=1)


@click.command()
@click.argument('from-file', required=True, type=click.Path(exists=True, dir_okay=False, file_okay=True))
def main(from_file: pathlib.Path):
    from_file = pathlib.Path(from_file)
    sig_algorithm = from_file
    cross = from_file
    kem_algorithm = from_file
    default_sig = "rsa:2048"
    default_kem = "X25519"

    d_sig, baseline1 = retrieve_sig_data(sig_algorithm, default_sig)
    d_kem, baseline2 = retrieve_kem_data(kem_algorithm, default_kem)
    d_level, baseline3 = retrieve_cross_data(cross, default_sig, default_kem)

    d_result = add_expectation(d_level, d_sig, d_kem, baseline1)

    print(d_result.to_csv(index_label="index"))


if __name__ == '__main__':
    main()

