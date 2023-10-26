#!/usr/bin/env python3

import argparse
import binascii
import cProfile
import logging
import sys

from pypacker import ppcap

from pypacker.layer12 import ethernet
from pypacker.layer3 import ip
from pypacker.layer4 import tcp as tcpP


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def extract_l4_protocols(buf):
    ipv4 = 0
    ipv6 = 0
    other = 0

    ipv4_no_header = 0
    tcp = 0
    udp = 0
    icmp = 0
    other_l4 = 0

    if buf[12:14] == b'\x08\x00':
        ipv4 = 1

        if buf[14:15] != b'\x45':
            ipv4_no_header = 1
            return buf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, other_l4

        protocol = buf[23:24]
        if protocol == b'\x06': # TCP
            tcp = 1

            return buf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, other_l4

        elif protocol == b'\x11': # UDP
            udp = 1
            return buf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, other_l4

        elif protocol == b'\x01': # ICMP
            icmp = 1
        else: # other l4 proto

            other_l4 = 1
            logging.debug("Detected unknown IPv4 payload with protocol number: %s", protocol)

    elif buf[12:14] == b'\x86\xdd':
        ipv6 = 1
    else:
        other = 1

    return buf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, other_l4


def extract_ipv4_data(eth):
    """
    Extracting general IPv4 data in our case only IP addresses
    :param eth:
    :return:
    """
    ip_data = eth[ip.IP]
    if ip_data is None:
        return {}
    return dict(src=ip_data.src_s, dst=ip_data.dst_s, len=ip_data.len, length=len(ip_data))


def extract_tcp_data(eth):
    """
    Extracting general TCP data from the TCP packet submitted through
    :param eth:
    :return:
    """
    tcp_packet = eth[tcpP.TCP]
    if tcp_packet is None:
        return {}
    push_flag = tcp_packet.flags & 0b1000 > 0
    return dict(header_len=tcp_packet.header_len, src=tcp_packet.sport, dst=tcp_packet.dport, seq=tcp_packet.seq, ack=tcp_packet.ack, flags=tcp_packet.flags_t if tcp_packet.flags_t != "" else "None", flags_i=tcp_packet.flags, push_flag=push_flag, body=tcp_packet.body_bytes, body_len=len(tcp_packet.body_bytes))


def extract_tls_data(payload):
    """
    Extract the TLS data from the payload
    :param payload:
    :return:
    """
    if payload is None:
        return {}

    tls_data = {}
    if payload[0:1] == b'\x16':  # handle client hello
        tls_data['protocol'] = "Handshake"
        if payload[5:6] == b'\x01':
            tls_data['type'] = "ClientHello"
        elif payload[5:6] == b'\x02':
            tls_data['type'] = "ServerHello"
        elif payload[5:6] == b'\x03':
            tls_data['type'] = "EndOfEarlyData"
        elif payload[5:6] == b'\x04':
            tls_data['type'] = "EncryptedExtensions"
        elif payload[5:6] == b'\x05':
            tls_data['type'] = "CertificateRequest"
        elif payload[5:6] == b'\x06':
            tls_data['type'] = "Certificate"
        elif payload[5:6] == b'\x07':
            tls_data['type'] = "CertificateVerify"
        elif payload[5:6] == b'\x07':
            tls_data['type'] = "Finished"
        elif payload[5:6] == b'\x08':
            tls_data['type'] = "NewSessionTicket"
        elif payload[5:6] == b'\x09':
            tls_data['type'] = "KeyUpdate"

        tls_data['session_len'] = int.from_bytes(payload[43:44], byteorder='little')
        if tls_data.get("session_len") > 0:
            tls_data['session_id'] = payload[44:(44+tls_data.get("session_len"))].hex()

    elif payload[0:1] == b'\x14':  # handle client change cipher Spec
        tls_data['protocol'] = "ChangeCipherSpec"

    return tls_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pcap")
    parser.add_argument("--profile")

    args = parser.parse_args()

    pcap = ppcap.Reader(args.pcap)

    stats_ipv4 = 0
    stats_ipv6 = 0
    stats_other = 0
    stats_ipv4_no_header = 0
    stats_tcp = 0
    stats_udp = 0
    stats_icmp = 0
    stats_other_l4 = 0

    profile = None
    if args.profile:
        profile = cProfile.Profile()
        profile.enable()

    try:
        for ts, buf in pcap:
            xbuf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, other_l4 = extract_l4_protocols(buf[:64])

            stats_ipv4 += ipv4
            stats_ipv6 += ipv6
            stats_other += other
            stats_ipv4_no_header += ipv4_no_header
            stats_tcp += tcp
            stats_udp += udp
            stats_icmp += icmp
            stats_other_l4 += other_l4

            if tcp == 1:  # At the moment are we only analyzing TCP
                eth = ethernet.Ethernet(buf)
                ip_data = extract_ipv4_data(eth)
                tcp_data = extract_tcp_data(eth)
                tcp_data_body = tcp_data.get('body')
                if tcp_data_body is None:
                    logging.error(f'Corrupt (last?) TCP Packet with empty body, stop')
                    break
                tcp_data_len = len(tcp_data_body)
                tls_data = extract_tls_data(tcp_data_body)

                try:
                    # ip src, ip dst, ip len, tcp header len, tcp src, tcp dst, tcp seq, tcp ack, tcp flags, TLS prot, TLS type, TLS Session ID Len, Session ID
                    sys.stdout.buffer.write(b"%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (ts,  bytes(str(ip_data.get("src")), encoding='utf8'),
                                                                                                               bytes(str(ip_data.get("dst")), encoding='utf8'),
                                                                                                               bytes(str(ip_data.get("len")), encoding='utf8'),
                                                                                                               bytes(str(tcp_data.get("header_len")), encoding='utf8'),
                                                                                                               bytes(str(tcp_data.get("src")), encoding='utf8'),
                                                                                                               bytes(str(tcp_data.get("dst")), encoding='utf8'),
                                                                                                               bytes(str(tcp_data.get("seq")), encoding='utf8'),
                                                                                                               bytes(str(tcp_data.get("ack")), encoding='utf8'),
                                                                                                               bytes(str(tcp_data.get("flags")), encoding='utf8'),
                                                                                                               bytes(str(tls_data.get("protocol", "None")), encoding='utf8'),
                                                                                                               bytes(str(tls_data.get("type", "None")), encoding='utf8'),
                                                                                                               bytes(str(tls_data.get("session_len", "None")), encoding='utf8'),
                                                                                                               bytes(str(tls_data.get("session_id", "None")), encoding='utf8'),
                                                                                                               bytes(str(tcp_data_len), encoding='utf8')))
                except BrokenPipeError as e:
                    logging.info("Broken Pipe (reader died?), exiting")
                    break
    # suppress error when executing in python 3.7
    # changed behavior of StopIteration
    except Exception as e:
        logging.error(f'Exception occured: {e}')
        pass

    if profile:
        profile.disable()
        profile.dump_stats(args.profile)

    logging.info("IPv4: %i [!options: %i] (TCP: %i, UDP: %i, ICMP: %i, other: %i), IPv6: %i, other: %i",
                 stats_ipv4, stats_ipv4_no_header, stats_tcp, stats_udp, stats_icmp, stats_other_l4, stats_ipv6, stats_other)


if __name__ == "__main__":
    main()