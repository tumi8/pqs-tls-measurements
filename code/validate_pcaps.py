#!/usr/bin/env python3
"""Reject incomplete or empty Ethernet PCAP files before analyzing a run."""

import argparse
import json
from pathlib import Path
import struct


def validate_pcap(path):
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(24)
        byte_orders = {
            b"\xd4\xc3\xb2\xa1": "<", b"\x4d\x3c\xb2\xa1": "<",
            b"\xa1\xb2\xc3\xd4": ">", b"\xa1\xb2\x3c\x4d": ">",
        }
        if len(header) != 24 or header[:4] not in byte_orders:
            raise ValueError(f"{path}: invalid PCAP header")
        endian = byte_orders[header[:4]]
        snaplen, linktype = struct.unpack(endian + "II", header[16:24])
        if linktype != 1:
            raise ValueError(f"{path}: expected an Ethernet capture")
        packets = 0
        while True:
            record = stream.read(16)
            if not record:
                break
            if len(record) != 16:
                raise ValueError(f"{path}: truncated record header")
            _, _, captured, original = struct.unpack(endian + "IIII", record)
            if not captured or captured > min(original, snaplen):
                raise ValueError(f"{path}: invalid captured packet length")
            if stream.tell() + captured > size:
                raise ValueError(f"{path}: truncated packet at byte {stream.tell()}")
            stream.seek(captured, 1)
            packets += 1
    if not packets:
        raise ValueError(f"{path}: empty capture")
    return {"file": str(path), "packets": packets, "bytes": size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcaps", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        results = [validate_pcap(path) for path in args.pcaps]
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps({"status": "PASS", "captures": results}, indent=2))


if __name__ == "__main__":
    main()
