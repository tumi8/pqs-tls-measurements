#!/usr/bin/env python3

import csv
import itertools
import logging
import pathlib
import sys

import click
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch

sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False, "axes.spines.left": False, "axes.spines.bottom": False})


def transform_traffic(df: pd.DataFrame, col, scale=1.5):
    df = pd.concat([df[col], df['clientServerBytes'] + df['serverClientBytes']], axis=1).rename(columns={0: 'traffic'}).sort_values(by='traffic')
    mask = df[col].apply(lambda x: any( item in x for item in ['90s', 'rsa:1024', 'rsa3075', 'rsa3072', '_aes'] ))
    df = df[ ~mask]
    df['traffic_log'] = np.log(df['traffic'])
    min_value = df['traffic_log'].min()
    max_value = df['traffic_log'].max()
    df['traffic_log'] = np.round(((df['traffic_log'] - min_value) / (max_value - min_value)) * scale, 1)
    df[col] = df.groupby('traffic_log')[col].transform(lambda x: ', '.join(x))
    return df[[col, 'traffic_log']].drop_duplicates()

def transform_latency(df: pd.DataFrame, col, col_latency, scale=.9):
    df = df[[col, col_latency]].sort_values(by=col_latency)
    mask = df[col].apply(lambda x: any( item in x for item in ['90s', 'rsa:1024', 'rsa3072', '_aes'] ))
    df = df[ ~mask]
    df['latency_log'] = np.log(df[col_latency])
    min_value = df['latency_log'].min()
    max_value = df['latency_log'].max()
    df['latency_log'] = np.round(((df['latency_log'] - min_value) / (max_value - min_value)) * scale, 1)
    df[col] = df.groupby('latency_log')[col].transform(lambda x: ', '.join(x))
    return df[[col, 'latency_log']].drop_duplicates()


def is_pre_quantum(alg: str):
    if len(alg) == 4 and alg.startswith('p'):
        return True
    if alg.startswith('rsa:'):
        return True
    if alg == 'X25519':
        return True
    return False
def is_hybrid(alg: str):
    return '_' in alg

def plot_line_with_labels(entries, labels, entries_b, labels_b, name: pathlib.Path, label_left: str, label_right: str, height=3.5):
    labels = labels.apply(lambda x: x.replace('\\', ''))
    labels_b = labels_b.apply(lambda x: x.replace('\\', ''))

    fig = plt.figure(figsize=(16, height))
    ax = plt.gca()

    ax.plot(pd.concat([entries, entries_b]).drop_duplicates(), np.zeros_like(pd.concat([entries, entries_b]).drop_duplicates()), "-o",
            color="k", markerfacecolor="w")

    colors = sns.color_palette()
    props_pq = dict(boxstyle='round', facecolor=colors[0], alpha=0.2)
    props_pre = dict(boxstyle='round', facecolor=colors[1], alpha=0.2)
    props_h = dict(boxstyle='round', facecolor=colors[2], alpha=0.2)
    # annotate lines

    highest_text = 0
    for d, r in zip(entries, labels):
        label = r.split(', ')
        label.sort(key= lambda x: len(x))
        levels = itertools.cycle([.2, 1.4, 2.6, 3.8, 5.0, 6.2])
        levels = range(20)
        if len(label) > highest_text:
            highest_text = len(label)
        for r, l in zip(label, levels):
            l = l * .7 + .22
            d2 = d
            if is_pre_quantum(r):
                props = props_pre
            elif is_hybrid(r):
                props = props_h
            else:
                props = props_pq
            ax.annotate(r, xy=(d2, l), rotation=0, family='monospace',
                    xytext=(-3, np.sign(l)*3), textcoords="offset points",
                    horizontalalignment="left",fontsize=9,
                    verticalalignment="bottom",bbox=props)
    lowest_text = 0
    for d, r in zip(entries_b, labels_b):
        label = r.split(', ')
        label.sort(key= lambda x: len(x), reverse=True)
        levels = range(20)
        if len(label) > lowest_text:
            lowest_text = len(label)
        for r, l in zip(label, levels):
            l = l * .7
            l = l * -1 - .6
            d2 = d
            if is_pre_quantum(r):
                props = props_pre
            elif is_hybrid(r):
                props = props_h
            else:
                props = props_pq
            ax.annotate(r, xy=(d2, l), rotation=0, family='monospace',
                    xytext=(-3, np.sign(l)*3), textcoords="offset points",
                    horizontalalignment="left",fontsize=9,
                    verticalalignment="bottom",bbox=props)

    left = np.min(entries)
    right = np.max(entries)
    ax.annotate(label_left, xy=(left-.01, 0), fontsize=12, horizontalalignment='right', verticalalignment='center')
    ax.annotate(label_right, xy=(right+.01, 0), fontsize=12, horizontalalignment='left',  verticalalignment='center')


    legend_elements = [ Patch(facecolor=c, edgecolor=c, label=l, alpha=.4) for c,l in zip(colors, ['Post-Quantum', 'Pre-Quantum', 'Hybrid'])]

    ax.legend(handles=legend_elements, loc='upper left', borderaxespad=0, bbox_to_anchor=(1.1, 1), ncol=1)

    # remove y-axis and spines
    ax.yaxis.set_visible(False)
    ax.xaxis.set_visible(False)
    #ax.spines[["left", "top", "right", "bottom"]].set_visible(False)
    fig.tight_layout()
    plt.ylim([-lowest_text, highest_text])

    #fig.autofmt_xdate(rotation=45)
    plt.savefig(f'{name}.pdf', bbox_inches='tight', pad_inches = 0)


@click.command()
@click.argument('latency-file', required=True, type=click.Path(exists=True, dir_okay=False, file_okay=True))
@click.argument('to-dir', required=True, type=click.Path(dir_okay=True, file_okay=False))
def analyse(latency_file: str, to_dir: str):
    logging.basicConfig(level=logging.INFO)
    latency_file = pathlib.Path(latency_file)
    to_dir = pathlib.Path(to_dir)
    to_dir.mkdir(exist_ok=True, parents=True)

    latency_df = pd.read_csv(latency_file)

    kem_latencies_df = transform_latency(latency_df, 'kem', 'partAllMedian', scale=.9)
    sig_latencies_df = transform_latency(latency_df, 'sig', 'partAllMedian', scale=.9)
    plot_line_with_labels(kem_latencies_df['latency_log'], kem_latencies_df['kem'], sig_latencies_df['latency_log'], sig_latencies_df['sig'],
                          to_dir / 'handshake_latency_ranked', 'fast', 'slow')

    kem_traffic_df = transform_traffic(latency_df, 'kem', scale=.9)
    sig_traffic_df = transform_traffic(latency_df, 'sig', scale=.9)
    plot_line_with_labels(kem_traffic_df['traffic_log'], kem_traffic_df['kem'], sig_traffic_df['traffic_log'], sig_traffic_df['sig'], to_dir / 'transmission_volume_ranked',
                          'low', 'high', height=3.25)


if __name__ == '__main__':
    analyse()
