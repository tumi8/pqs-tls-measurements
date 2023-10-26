from pathlib import Path, PurePath
import re
from jinja2 import Environment, FileSystemLoader
import argparse
import csv
import logging
import yaml
import sys

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("data_folder", help="location of the data folder")
parser.add_argument("result_folder", help="location of the original results (containing *.loop files)")
parser.add_argument("-v", "--verbose",  help="print debug output", action="store_true")
args = parser.parse_args()

# configure logging
if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

# read folder paths
dataFolder = Path(args.data_folder)
resultFolder = Path(args.result_folder)
templateFolder = Path('./template')

env = Environment(loader=FileSystemLoader(templateFolder))


def check_data_folder():
    logging.debug('checking figures folder')
    logging.debug(dataFolder)


check_data_folder()


loops = {}


def check_result_folder():
    logging.debug('checking result folder')
    loop_files = sorted(list(resultFolder.glob('*.loop')))
    if len(loop_files) == 0:
        logging.error("no loop files found. wrong result folder?")
        sys.exit(0)
    for loop in loop_files:
        with open(loop, "r") as stream:
            run = re.findall(r'run\d+', loop.stem)[-1].replace('run', '')
            try:
                loops[run] = {}
                loops[run]["loop_var"] = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logging.error(exc)
                sys.exit(0)


check_result_folder()


def check_result_file():
    logging.debug('checking result files from client')
    results_files = sorted(list(resultFolder.glob('opensslclient_run*.stdout')))
    for i in results_files:
        run = re.findall(r'run\d+', i.stem)[-1].replace('run', '')
        loops[run]["result_file"] = i


check_result_file()


def extract_data():
    logging.debug('extracting data for results files from client')
    for i in loops:
        with open(loops[i]["result_file"], "rt", encoding="utf-8") as result_file:
            data = result_file.readlines()
        for line in data:
            if "connections/user sec" in line:
                search_res_tmp = re.findall(r'(\d+) connections in (\d+.\d+)s; (\d+.\d+|inf)', line)
                loops[i]["connections"] = int(search_res_tmp[0][0])
                loops[i]["time"] = float(search_res_tmp[0][1])
                loops[i]["connections_per_user_sec"] = "inf" if search_res_tmp[0][2] == "inf" else float(search_res_tmp[0][2])
            if "bytes read per connection" in line:
                search_res_tmp = re.findall(r'in (\d+) real seconds', line)
                loops[i]["real_seconds"] = int(search_res_tmp[0])


extract_data()


def save_csv():

    header = ["run", "run_vars", "connections", "time", "connections_per_user_sec", "real_seconds"]

    with open(dataFolder / "client_results.csv", 'w', encoding='UTF8') as f:
        writer = csv.writer(f)

        # write header first
        writer.writerow(header)

        for i in loops:
            loop = loops[i]
            writer.writerow([
                i,
                loop.get("loop_var"),
                loop.get("connections"),
                loop.get("time"),
                loop.get("connections_per_user_sec"),
                loop.get("real_seconds")
            ])


save_csv()
