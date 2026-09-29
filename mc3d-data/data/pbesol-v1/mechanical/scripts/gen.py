#!/usr/bin/env python
"""Generate mechanical ``base.json`` data from elastic and supercon archives."""

import argparse
import json
import sys
from pathlib import Path

from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from mcxd_web_pipeline.utils import dump_canonical_json
from util import (
    parse_moduli,
    load_thermo_pw,
    load_matdyn,
    load_scon,
    calculate_c,
    check_base_json,
)

SUPERCON_ARCHIVE_URL = "https://doi.org/10.24435/materialscloud:n9-a7"

GROUP_FD_PSEUDODOJO   = "paper/FD/PseudoDojo"
GROUP_FD_SSSP         = "paper/FD/SSSP"
GROUP_BORN_PSEUDODOJO = "paper/Born/PseudoDojo"
GROUP_BORN_SSSP_07 = "paper/Born/SSSP/q0.7"
GROUP_BORN_SSSP_05 = "paper/Born/SSSP/q0.5"
GROUP_BORN_SSSP_03 = "paper/Born/SSSP/q0.3"

GROUP_SCON = 'paper/workchains/scon'    

def log(msg):
    print(msg, file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Generate mechanical base data, including its superconductivity-derived descriptor."
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
        "-e",
        "--elastic-file",
        metavar="ARCHIVE_FILE",
        type=Path,
        help="Path to the mechanical elastic.aiida archive.",
    )

    group.add_argument(
        "-f",
        "--file",
        metavar="FILE_PATH",
        type=str,
        help="The path to the `base.json` file to load. The script will load the data from this file.",
    )

    parser.add_argument(
        "--supercon-file",
        metavar="ARCHIVE_FILE",
        type=Path,
        help=(
            "Path to the required superconductivity EPW-screening.aiida archive. "
            f"Download it from {SUPERCON_ARCHIVE_URL}."
        ),
    )

    parser.add_argument(
        "--output",
        metavar="BASE_JSON",
        type=Path,
        required=True,
        help="New path for the generated base.json. Existing files are never overwritten without --force.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --output to overwrite an existing file.",
    )

    parser.add_argument(
        "-nb",
        "--no_born",
        action="store_true",
        help="Do not load the born charges.",
    )

    args = parser.parse_args()

    if args.supercon_file and not args.elastic_file:
        parser.error("--supercon-file can only be used together with --elastic-file.")
    if args.elastic_file and not args.supercon_file:
        parser.error(
            "--elastic-file requires --supercon-file. "
            f"Download EPW-screening.aiida from {SUPERCON_ARCHIVE_URL}."
        )

    output_path = args.output.resolve()
    if not output_path.parent.is_dir():
        parser.error(f"Output directory does not exist: {output_path.parent}")
    if output_path.exists() and not args.force:
        parser.error(f"Refusing to overwrite {output_path}. Use --force only after reviewing the file.")

    details = {}

    if args.file:
        with open(args.file, "r") as handle:
            details = json.load(handle)
    elif args.profile:
        for group, pseudo in [
            (GROUP_FD_PSEUDODOJO, "PseudoDojo"), 
            (GROUP_FD_SSSP, "SSSP")
            ]:
            load_thermo_pw(args.profile, group, pseudo, parser=parse_moduli, details=details)
        for group, pseudo, qdensity in [
            (GROUP_BORN_PSEUDODOJO, "PseudoDojo", 0.5),
            (GROUP_BORN_SSSP_07, "SSSP", 0.7),
            (GROUP_BORN_SSSP_05, "SSSP", 0.5),
            (GROUP_BORN_SSSP_03, "SSSP", 0.3)
        ]:
            load_matdyn(args.profile, group, pseudo, qdensity, details=details)
        supercon_count = load_scon(args.profile, GROUP_SCON, log=log, details=details)

    elif args.elastic_file:
        elastic_archive = args.elastic_file
        supercon_archive = args.supercon_file
        if not elastic_archive.is_file():
            parser.error(f"Missing elastic archive: {elastic_archive}")
        if not supercon_archive.is_file():
            parser.error(
                f"Missing superconductivity archive: {supercon_archive}. "
                f"Download EPW-screening.aiida from {SUPERCON_ARCHIVE_URL}."
            )

        archive_profile = SqliteZipBackend.create_profile(elastic_archive)
        for group, pseudo in [
            (GROUP_FD_PSEUDODOJO, "PseudoDojo"), 
            (GROUP_FD_SSSP, "SSSP")
            ]:
            load_thermo_pw(archive_profile, group, pseudo, parser=parse_moduli, details=details)
        if not args.no_born:
            for group, pseudo, qdensity in [
                (GROUP_BORN_PSEUDODOJO, "PseudoDojo", 0.5),
                (GROUP_BORN_SSSP_07, "SSSP", 0.7),
                (GROUP_BORN_SSSP_05, "SSSP", 0.5),
                (GROUP_BORN_SSSP_03, "SSSP", 0.3)
            ]:
                load_matdyn(archive_profile, group, pseudo, qdensity, details=details)
        archive_profile = SqliteZipBackend.create_profile(supercon_archive)
        supercon_count = load_scon(
            archive_profile,
            GROUP_SCON,
            log=log,
            details=details,
        )
    else:
        print(
            "You must provide one of the following parameters: --file, --profile or --elastic-file.",
            file=sys.stderr,
        )
        parser.print_help()
        sys.exit(1)

    if not args.file and not supercon_count:
        parser.error(
            "No superconductivity data was found in the supplied AiiDA source. "
            f"Import or supply EPW-screening.aiida from {SUPERCON_ARCHIVE_URL}."
        )

    calculate_c(details)

    check_base_json(details)

    with output_path.open("w") as handle:
        dump_canonical_json(details, handle)

    log("Done!")


if __name__ == "__main__":
    main()
