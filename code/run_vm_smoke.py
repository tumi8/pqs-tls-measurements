#!/usr/bin/env python3
"""Run one validated CoNEXT TLS smoke case with Docker Compose on a VM."""

import argparse
import csv
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time

from validate_pcaps import validate_pcap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kem", choices=("X25519", "kyber768", "p384_kyber768"), default="X25519")
    parser.add_argument("--seconds", type=int, default=5)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600:
        parser.error("--seconds must be between 1 and 3600")
    output = args.output.resolve()
    if output.exists():
        parser.error("choose a new output directory; existing results are never overwritten")
    if not shutil.which("docker") or not shutil.which("git"):
        parser.error("install Docker Engine, the Compose plugin and Git first")
    code_dir = Path(__file__).resolve().parent
    source_commit = subprocess.check_output(
        ["git", "-C", str(code_dir), "rev-parse", "HEAD"], text=True
    ).strip()
    engine = subprocess.check_output(
        ["docker", "info", "--format", "{{.NCPU}} {{.OSType}} {{.Architecture}}"], text=True
    ).split()
    if int(engine[0]) < 2 or engine[1] != "linux" or engine[2] not in ("x86_64", "amd64"):
        parser.error("this reproduction needs a Linux amd64 Docker engine with CPU 1 available")
    environment = os.environ.copy()
    environment.update({
        "CPU_PROFILING": "False", "RUN": "000", "KEM_ALG": args.kem,
        "SIG_ALG": "rsa:2048", "NETEM_TC": "", "HOST_DIR": str(output),
        "OUT_DIR": str(output), "EXPERIMENT": "vm-smoke", "DEVIATION_ANALYSIS": "False",
    })
    compose = ["docker", "compose", "--project-name", "pqc-conext2023",
               "--file", str(code_dir / "docker-compose.yml")]
    existing = subprocess.check_output(
        compose + ["ps", "--all", "--quiet"], env=environment, stderr=subprocess.DEVNULL, text=True
    ).strip()
    if existing:
        parser.error("the pqc-conext2023 Compose project is already in use")
    (output / "client").mkdir(parents=True)
    (output / "server").mkdir()
    (output / "environment.json").write_text(json.dumps({
        "host": platform.platform(), "docker_cpus": int(engine[0]), "docker_architecture": engine[2],
        "source_commit": source_commit, "measurement_seconds_requested": args.seconds,
        "key_exchange": args.kem, "signature": "rsa:2048", "cpu_profiling": False, "netem": "",
    }, indent=2) + "\n", encoding="utf-8")
    started = False
    with (output / "docker.log").open("w", encoding="utf-8") as log:
        def command(arguments, capture=False):
            log.write("$ " + " ".join(arguments) + "\n")
            log.flush()
            completed = subprocess.run(
                arguments, cwd=code_dir, env=environment,
                stdout=subprocess.PIPE if capture else log,
                stderr=subprocess.STDOUT, text=True, errors="replace", check=True,
            )
            if capture:
                log.write(completed.stdout)
                log.flush()
                return completed.stdout
            return ""

        try:
            command(compose + ["config", "--quiet"])
            if not args.skip_build:
                print(f"Building client/server; progress: {output / 'docker.log'}", flush=True)
                command(compose + ["--progress", "plain", "build", "client", "server"])
            print(f"Starting {args.kem} with RSA-2048 server authentication", flush=True)
            started = True
            command(compose + ["up", "--detach", "--no-build", "server"])
            deadline = time.monotonic() + 60
            while "ACCEPT" not in command(compose + ["logs", "--no-color", "server"], capture=True):
                if time.monotonic() >= deadline:
                    raise RuntimeError("TLS server did not become ready in 60 seconds")
                time.sleep(1)
            command(compose + ["run", "--rm", "--no-deps", "-T", "--env",
                               f"MEASUREMENT_TIME={args.seconds}", "client"])
            command(compose + ["exec", "-T", "server", "pkill", "-INT", "tcpdump"])
            command(compose + ["stop", "server"])
            stdout = (output / "client/opensslclient_run000.stdout").read_text(encoding="utf-8")
            count = re.search(r"(\d+) connections in [\d.]+s; (?:[\d.]+|inf) connections/user sec", stdout)
            elapsed = re.search(r"in ([\d.]+) real seconds", stdout)
            if not count or not elapsed or int(count[1]) <= 0 or float(elapsed[1]) <= 0:
                raise RuntimeError("OpenSSL did not report a successful measurement")
            captures = [validate_pcap(output / filename) for filename in (
                "client/latencies-post_run000.pcap", "server/latencies-pre_run000.pcap")]
            (output / "pcap-validation.json").write_text(
                json.dumps({"status": "PASS", "captures": captures}, indent=2) + "\n", encoding="utf-8")
            result = {
                "key_exchange": args.kem, "signature": "rsa:2048", "tls_mode": "server-authenticated",
                "connections": int(count[1]), "measurement_seconds_requested": args.seconds,
                "real_seconds_reported": float(elapsed[1]),
                "connections_per_real_second": round(int(count[1]) / float(elapsed[1]), 3),
                "source_commit": source_commit, "validation_only": True,
                "image_id": command(["docker", "image", "inspect", "pqc-conext2023-client",
                                     "--format", "{{.Id}}"], capture=True).strip(),
            }
            (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            with (output / "result.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(result))
                writer.writeheader()
                writer.writerow(result)
            print(f"PASS: {result['connections']} connections; complete captures in {output}", flush=True)
        finally:
            if started:
                subprocess.run(compose + ["logs", "--no-color", "server"], env=environment,
                               stdout=log, stderr=subprocess.STDOUT, check=False)
                cleanup = subprocess.run(compose + ["down", "--volumes", "--remove-orphans"],
                                         env=environment, stdout=log, stderr=subprocess.STDOUT, check=False)
                if cleanup.returncode:
                    print(f"WARNING: cleanup failed; see {output / 'docker.log'}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"FAILED: {error}")
