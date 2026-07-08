#!/usr/bin/env python
"""
This script is used to generate the base.json file from aiida archives QE-screening.aiida and EPW-screening.aiida.
"""

import argparse
import json
import sys
from pathlib import Path

from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from mcxd_web_pipeline.utils import dump_canonical_json
from util import (
    load_thermo_pw,
    load_matdyn,
    check_base_json,
)

OUTPUT_PATH = Path().resolve().parent
LOG_DST = Path().resolve() / "log"

# 1. QE-screening.aiida
# This archive contains all the information for the interactive phonon section.
ARCHIVE_ELASTIC       = "elastic.aiida"
GROUP_FD_PSEUDODOJO   = "paper/FD/PseudoDojo"
GROUP_FD_SSSP         = "paper/FD/SSSP"
GROUP_BORN_PSEUDODOJO = "paper/Born/PseudoDojo"
GROUP_BORN_SSSP       = "paper/Born/SSSP"

def log(msg):
    with open(LOG_DST, "a") as f:
        f.write(str(msg) + "\n")



def main():
    parser = argparse.ArgumentParser(
        description="A script to generate the base.json file from aiida archives QE-screening.aiida and EPW-screening.aiida."
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-p",
        "--profile",
        metavar="PROFILE_NAME",
        type=str,
        help="The name of the AiiDA profile. The script will assume that the data exists in this profile.",
    )

    group.add_argument(
        "-a",
        "--archive",
        metavar="ARCHIVE_PATH",
        type=str,
        help="The path to the AiiDA archive file (.aiida). The script will import data from this file.",
    )

    group.add_argument(
        "-f",
        "--file",
        metavar="FILE_PATH",
        type=str,
        help="The path to the `base.json` file to load. The script will load the data from this file.",
    )

    args = parser.parse_args()

    details = {}

    if args.file:
        with open(args.file, "r") as handle:
            details = json.load(handle)
    elif args.profile:
        archive_profile = SqliteZipBackend.create_profile(args.profile)
        load_thermo_pw(archive_profile, details=details)
        load_matdyn(archive_profile, details=details)
    elif args.archive:
        AIIDA_PROFILE_NAME = Path(args.archive) / ARCHIVE_ELASTIC
        archive_profile = SqliteZipBackend.create_profile(AIIDA_PROFILE_NAME)
        load_thermo_pw(archive_profile, pp = 'PseudoDojo', details=details, label=GROUP_FD_PSEUDODOJO)
        load_thermo_pw(archive_profile, pp = 'SSSP', details=details, label=GROUP_FD_SSSP)
        load_matdyn(archive_profile, pp = 'PseudoDojo', qdensity="0.5", details=details, label=GROUP_BORN_PSEUDODOJO)

    else:
        print(
            "You must provide one of the following parameters: --file, --profile or --archive.",
            file=sys.stderr,
        )
        parser.print_help()
        sys.exit(1)

    check_base_json(details)
    # Save the base.json file
    with (OUTPUT_PATH / "base.json").open("w") as handle:
        dump_canonical_json(details, handle)

    log("Done!")


if __name__ == "__main__":
    main()
