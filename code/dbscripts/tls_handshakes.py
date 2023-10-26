#!/usr/bin/env python3

import csv
import logging
import sys

import click
from pypacker import ppcap
from pypacker.layer12 import ethernet

from pcaptocsv import extract_l4_protocols, extract_ipv4_data, extract_tcp_data, extract_tls_data

logger = logging.getLogger()


@click.command()
@click.argument('pre', type=click.Path(file_okay=True, dir_okay=False, exists=True))
@click.argument('post', type=click.Path(file_okay=True, dir_okay=False, exists=True))
def main(pre, post):
    pre_pcap = ppcap.Reader(pre)
    post_pcap = ppcap.Reader(post)

    handshake_start = None
    handshake_response = None
    handshake_c_packets = None
    handshake_c_bytes = 0
    handshake_s_packets = None
    handshake_s_bytes = 0
    handshake_s_pushs = 0
    phase = None

    csv_writer = csv.DictWriter(sys.stdout, fieldnames=['handshake_start', 'handshake_response', 'handshake_duration', 'handshake_c_packets', 'handshake_s_packets', 'handshake_s_tcp_pushs', 'handshake_s_bytes', 'handshake_c_bytes'])
    csv_writer.writeheader()

    for source, ts, ip_data, tcp_data, tls_data in tls_reader(pre_pcap, post_pcap):
        if source == 'post' and tcp_data.get('push_flag'):
            handshake_s_pushs += 1
        if source == 'pre' and ip_data is not None and ip_data.get('length'):
            handshake_c_bytes += ip_data.get('length')
        if source == 'post' and ip_data is not None and ip_data.get('length'):
            handshake_s_bytes += ip_data.get('length')
        if source == 'pre' and tls_data.get('type') == 'ClientHello':
            handshake_start = ts
            handshake_response = None
            handshake_c_packets = 1
            handshake_c_bytes = ip_data.get('length')
            handshake_s_packets = 0
            handshake_s_bytes = 0
            handshake_s_pushs = 0
            phase = 'ch'
        elif phase == 'ch' and source == 'pre' and tcp_data.get('body_len') > 0:
            handshake_c_packets += 1
        elif phase =='ch' and source == 'post' and tls_data.get('type') == 'ServerHello':
            handshake_s_packets += 1
            handshake_response = ts
            phase = 'sh'
        elif phase == 'sh' and source == 'post' and tcp_data.get('body_len') > 0:
            handshake_s_packets += 1
        elif phase == 'sh' and source == 'pre' and tls_data.get('protocol') == "ChangeCipherSpec":
            csv_writer.writerow({
                'handshake_start': handshake_start,
                'handshake_response': handshake_response - handshake_start,
                'handshake_duration': ts - handshake_start,
                'handshake_c_packets': handshake_c_packets,
                'handshake_c_bytes': handshake_c_bytes,
                'handshake_s_packets': handshake_s_packets,
                'handshake_s_bytes': handshake_s_bytes,
                'handshake_s_tcp_pushs': handshake_s_pushs,
            })


def tls_reader(pre: ppcap.Reader, post: ppcap.Reader):
    try:
        pre_packet_ts, pre_packet = pre.__next__()
        post_packet_ts, post_packet = post.__next__()
    except StopIteration:
        return
    while True:
        try:
            if pre_packet_ts < post_packet_ts:
                ip_data, tcp_data, tls_data = parse_tls_packet(pre_packet)
                if tls_data is not None:
                    yield 'pre', pre_packet_ts, ip_data, tcp_data, tls_data
                pre_packet_ts, pre_packet = pre.__next__()
            else:
                ip_data, tcp_data, tls_data = parse_tls_packet(post_packet)
                if tls_data is not None:
                    yield 'post', post_packet_ts, ip_data, tcp_data, tls_data
                post_packet_ts, post_packet = post.__next__()
        except StopIteration:
            break
        except Exception as ex:
            logger.exception("Error parsing pcap", exc_info=ex)
            break


def parse_tls_packet(buf):
    xbuf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, other_l4 = extract_l4_protocols(buf[:64])

    if tcp == 1:  # At the moment are we only analyzing TCP
        eth = ethernet.Ethernet(buf)
        ip_data = extract_ipv4_data(eth)
        tcp_data = extract_tcp_data(eth)
        tls_data = extract_tls_data(tcp_data.get("body"))
        return ip_data, tcp_data, tls_data
    return None, None, None


if __name__ == "__main__":
    main()
