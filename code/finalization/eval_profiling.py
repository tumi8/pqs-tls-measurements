#!/usr/bin/python3

import os
import re
import csv
import math
import json
import pathlib
import argparse

replace_list = [("sphincsharaka", "sphincs"), ("fsimple", ""), ("frobust", ""), ("prime256v1", "p256"), ("secp384r1", "p384"), ("secp384r1", "p384"), ("secp521r1", "p521")]

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


pre_q_kem = ["X25519", "prime256v1", "secp384r1", "secp521r1"]
pre_q_sig = ["rsa:1024", "rsa:2048", "rsa:3072", "rsa:4096"]


### Parse perf report file
def load_perf_file(file_path):
    content = dict()
    with open(file_path, "r") as file_p:
        for line in file_p:
            if not line.rstrip() or line.startswith("#"):
                continue
            parsed = re.findall(r'\d+.\d+%|\S+', line)
            if len(parsed) < 3:
                print("Could not parse line: ", line.rstrip())
                continue
            elif len(parsed) > 3:
                parsed[3] = " ".join(parsed[3:])
            content[parsed[3]] = (float(parsed[0].strip("%")), parsed[1])

    return content

def strip_names(str_text, replace_list):

    for item in replace_list:
        str_text = str_text.replace(item[0], item[1])

    return str_text

parser = argparse.ArgumentParser(description="evaluate results and create table")
parser.add_argument('input_folder', type=pathlib.Path, help="input folder")
parser.add_argument('output_csv', type=pathlib.Path, help="output csv file")
args = parser.parse_args()

data = []
duplicate_detection = []

filepath = os.path.join(args.input_folder, "client_results.csv")
with open(filepath, newline='') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    for line in reader:
        json_obj = json.loads(line[1].replace("'", '"'))
        kem = json_obj["kem_alg"]
        sig = json_obj["sig_alg"]

        run_id = line[0]

        hs = int(line[2])
        duration = int(line[5])
        hs1s = math.ceil(hs / duration)

        # Load perf so file
        client_file_name = "perf-client_run" + run_id + ".data.txt"
        server_file_name = "perf-server_run" + run_id + ".data.txt"
        data_client = load_perf_file(os.path.join(args.input_folder, client_file_name))
        data_server = load_perf_file(os.path.join(args.input_folder, server_file_name))

        cost_client = sum([int(item[1][1]) for item in data_client.items()])
        cost_server = sum([int(item[1][1]) for item in data_server.items()])
        cost_hs_client = f"{cost_client / hs / 10**6:.2f}"
        cost_hs_server = f"{cost_server / hs / 10**6:.2f}"

        if kem+sig in duplicate_detection:
            continue
        duplicate_detection.append(kem+sig)

        kem_strip = strip_names(kem, replace_list)
        sig_strip = strip_names(sig, replace_list)

        data.append(dict(kem=kem_strip, sig=sig_strip, hs=hs, hs1s=hs1s, cost_hs_client=cost_hs_client, cost_hs_server=cost_hs_server, data_client=data_client, data_server=data_server))

with open(args.output_csv, 'w', newline='') as file:
    writer = csv.writer(file)
    field = ["kem", "sig", "hs", "hs1s", "cost_hs_server_ms", "cost_hs_client_ms", "server_libcrypto.so.1.1", "server_kernel.kallsyms", "server_libssl.so.1.1", "server_libc-2.31.so", "server_ixgbe", "server_python3.9", "client_libcrypto.so.1.1", "client_kernel.kallsyms", "client_libssl.so.1.1", "client_libc-2.31.so", "client_ixgbe", "client_python3.9"]
    writer.writerow(field)

    for element in data:

        field = list()
        field.append(element["kem"])
        field.append(element["sig"])
        field.append(element["hs"])
        field.append(element["hs1s"])
        field.append(element["cost_hs_server"])
        field.append(element["cost_hs_client"])
        field.append(element["data_server"].get("libcrypto.so.1.1", (0,))[0])
        field.append(element["data_server"].get("[kernel.kallsyms]", (0,))[0])
        field.append(element["data_server"].get("libssl.so.1.1", (0,))[0])
        field.append(element["data_server"].get("libc-2.31.so", (0,))[0])
        field.append(element["data_server"].get("[ixgbe]", (0,))[0])
        field.append(element["data_server"].get("python3.9", (0,))[0])
        field.append(element["data_client"].get("libcrypto.so.1.1", (0,))[0])
        field.append(element["data_client"].get("[kernel.kallsyms]", (0,))[0])
        field.append(element["data_client"].get("libssl.so.1.1", (0,))[0])
        field.append(element["data_client"].get("libc-2.31.so", (0,))[0])
        field.append(element["data_client"].get("[ixgbe]", (0,))[0])
        field.append(element["data_client"].get("python3.9", (0,))[0])

        writer.writerow(field)
