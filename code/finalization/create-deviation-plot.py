#!/usr/bin/env python3

import csv
import logging
import pathlib
import sys

import click
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
sns.set_theme(style="ticks")


def create_plot(df: pd.DataFrame, to_file: pathlib.Path):
    fig1, ax1 = plt.subplots(1, figsize=(4.5, 2.5))

    sns.scatterplot(data=df, ax=ax1, x="variance", y="sig", hue="kem", style='kem', legend='brief')  # ,

    plt.ylabel(None)

    ax1.legend(bbox_to_anchor=(1.25, 1), loc='upper left', borderaxespad=0, title='Key Agreement')

    ax1.set_xlabel('Deviation from Expected Latency [ms]')

    ax1.annotate('faster >', xy=(1, -.066), xytext=(5, 0), ha='left', va='top',
                 xycoords='axes fraction', textcoords='offset points')
    ax1.annotate('< slower', xy=(-.05, -.066), xytext=(5, 0), ha='right', va='top',
                 xycoords='axes fraction', textcoords='offset points')

    plt.savefig(f'{to_file}.pdf', bbox_inches='tight', pad_inches=0)


@click.command()
@click.argument('deviation-file', required=True, type=click.Path(exists=True, dir_okay=False, file_okay=True))
@click.argument('to-file', required=True, type=click.Path(exists=False, dir_okay=False, file_okay=True))
def analyse(deviation_file: str, to_file: str):
    logging.basicConfig(level=logging.INFO)
    deviation_file = pathlib.Path(deviation_file)
    to_file = pathlib.Path(to_file)

    deviation_df = pd.read_csv(deviation_file).sort_values(['kem', 'sig'], axis=0)
    deviation_df['kem'] = deviation_df['kem'].str.replace('\\_', '_')
    deviation_df['sig'] = deviation_df['sig'].str.replace('\\_', '_')

    create_plot(deviation_df, to_file)


if __name__ == '__main__':
    analyse()
