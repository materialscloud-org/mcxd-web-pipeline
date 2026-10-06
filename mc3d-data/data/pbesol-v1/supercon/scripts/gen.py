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
from supercon import (
    check_base_json,
    find_finest_qdensity,
    load_aniso,
    load_epw,
    load_epw_int_banddata,
    load_matdyn_from_elph,
    load_qe_el_banddata,
    load_scf_from_elph,
    load_scon,
)

LOG_DST = Path().resolve() / "log"

# QE-screening.aiida contains all information for the interactive phonon section.
GROUP_ELPH_03 = "paper/workchains/elph/q0.3"
GROUP_ELPH_05 = "paper/workchains/elph/q0.5"
GROUP_ELPH_07 = "paper/workchains/elph/q0.7"
GROUP_INTERACTIVE_PHONON_03 = "paper/workchains/phbands-qe/q0.3/matdyn"
GROUP_INTERACTIVE_PHONON_05 = "paper/workchains/phbands-qe/q0.5/matdyn"
GROUP_INTERACTIVE_PHONON_07 = "paper/workchains/phbands-qe/q0.7/matdyn"

# EPW-screening.aiida contains the information for the supercon section.
GROUP_SCON = "paper/workchains/scon"
GROUP_EPW = "paper/workchains/epw/stable"
GROUP_RESUBMISSION_EPW = "paper/for-resubmission/epw"
GROUP_BANDS_QE = "discover/bands-qe"
GROUP_BANDS_INT = "discover/bands-int"
GROUP_ANISO_GAP_FUNCTIONS = "discover/aniso_gap_functions"
GROUP_RESUBMISSION_BANDS = "paper/for-resubmission/bands"


def log(msg):
    with open(LOG_DST, "a") as f:
        f.write(str(msg) + "\n")


def load_supercon(archive_profile, log=log, details={}):
    ### Collect all the information for the superconductivity section
    log("Firstly we collect all the information for the superconductivity section")

    log("Loading spectral function and isotropic Tc...")
    load_scon(archive_profile, GROUP_SCON, log=log, details=details)
    log("Done!")

    ### Manual information for the superconductivity section
    iso_info_manual = {
        # H2V8
        "mc3d-26700": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 50,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [36, 36, 36],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [18, 18, 18],
                    "uuid": None,
                },
                "smearing_q": 1.8,
            }
        },
        # S4V4
        "mc3d-47379": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 40,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [36, 48, 36],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [18, 24, 18],
                    "uuid": None,
                },
                "smearing_q": 0.5,
            }
        },
        # Co2Mo2P4
        "mc3d-55964": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 40,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [46, 46, 18],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [23, 23, 9],
                    "uuid": None,
                },
                "smearing_q": 0.5,
            }
        },
        # Sn2Ti6
        "mc3d-4079": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 44,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [36, 36, 36],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [18, 18, 18],
                    "uuid": None,
                },
                "smearing_q": 0.3,
            }
        },
        # Ge3Hf3Rh3
        "mc3d-45112": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 48,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [40, 40, 56],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [20, 20, 28],
                    "uuid": None,
                },
                "smearing_q": 0.3,
            }
        },
        # P3Ru3Sc3
        "mc3d-49942": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 48,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [40, 40, 56],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [20, 20, 28],
                    "uuid": None,
                },
                "smearing_q": 0.5,
            }
        },
        # As2V6
        "mc3d-15151": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 44,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [32, 32, 32],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [16, 16, 16],
                    "uuid": None,
                },
                "smearing_q": 0.3,
            }
        },
        # Co2P4W2
        "mc3d-51658": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 40,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [40, 40, 16],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [20, 20, 8],
                    "uuid": None,
                },
                "smearing_q": 0.5,
            }
        },
        # Mo6Pb2
        "mc3d-42835": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 44,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [32, 32, 32],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [16, 16, 16],
                    "uuid": None,
                },
                "smearing_q": 0.3,
            }
        },
        # Ge2Nb6
        "mc3d-65870": {
            "supercon": {
                "type": "FBW",
                "number_of_wannier_functions": 44,
                "fermi_window": 0.8,
                "kgrid_epw_fine": {
                    "mesh": [50, 50, 50],
                    "uuid": None,
                },
                "qgrid_epw_fine": {
                    "mesh": [25, 25, 25],
                    "uuid": None,
                },
                "smearing_q": 0.3,
            }
        },
    }

    for k, v in iso_info_manual.items():
        details[k]["supercon"].update(v["supercon"])

    for group_epw, loading_function in [
        (GROUP_EPW, load_epw),
        (GROUP_RESUBMISSION_EPW, load_epw),
        (GROUP_BANDS_QE, load_qe_el_banddata),
        (GROUP_BANDS_INT, load_epw_int_banddata),
        (GROUP_ANISO_GAP_FUNCTIONS, load_aniso),
    ]:
        log(f"Loading workchains from {group_epw}...")
        loading_function(archive_profile, group_epw, log=log, details=details)
        log("Done!")


def load_visualize_phonon(archive_profile, log=log, details={}):
    ### Collect all the information for the interactive phonon section
    log("Secondly we collect all the information for the interactive phonon section")

    for qdensity, group_interactive_phonon, group_elph in [
        ("07", GROUP_INTERACTIVE_PHONON_07, GROUP_ELPH_07),
        ("05", GROUP_INTERACTIVE_PHONON_05, GROUP_ELPH_05),
        ("03", GROUP_INTERACTIVE_PHONON_03, GROUP_ELPH_03),
    ]:
        log(
            f"Loading Quantum ESPRESSO phonon bands and modes for stable phonons with qdensity {qdensity}..."
        )
        load_matdyn_from_elph(
            archive_profile,
            group_interactive_phonon,
            qdensity=qdensity,
            check_stability=True,
            log=log,
            details=details,
        )
        log("Done!")

        log(f"Loading Quantum ESPRESSO scf calcjobs with qdensity {qdensity}...")
        load_scf_from_elph(
            archive_profile, 
            group_elph, 
            qdensity=qdensity, 
            log=log, 
            details=details
        )
        log("Done!")


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
        "--qe-file",
        metavar="ARCHIVE_FILE",
        type=Path,
        help="Path to the QE-screening.aiida archive.",
    )

    group.add_argument(
        "-f",
        "--file",
        metavar="FILE_PATH",
        type=str,
        help="The path to the `base.json` file to load. The script will load the data from this file.",
    )

    parser.add_argument(
        "--epw-file",
        metavar="ARCHIVE_FILE",
        type=Path,
        help="Path to the EPW-screening.aiida archive.",
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

    args = parser.parse_args()

    if args.epw_file and not args.qe_file:
        parser.error("--epw-file can only be used together with --qe-file.")
    if args.qe_file and not args.epw_file:
        parser.error("--qe-file requires --epw-file.")

    output_path = args.output.resolve()
    if not output_path.parent.is_dir():
        parser.error(f"Output directory does not exist: {output_path.parent}")
    if output_path.exists() and not args.force:
        parser.error(
            f"Refusing to overwrite {output_path}. Use --force only after reviewing the file."
        )

    details = {}

    if args.file:
        with open(args.file, "r") as handle:
            details = json.load(handle)
    elif args.profile:
        load_supercon(args.profile, details=details)
        load_visualize_phonon(args.profile, details=details)
    elif args.qe_file:
        if not args.qe_file.is_file():
            parser.error(f"Missing QE archive: {args.qe_file}")
        if not args.epw_file.is_file():
            parser.error(f"Missing EPW archive: {args.epw_file}")

        archive_profile = SqliteZipBackend.create_profile(args.epw_file)
        load_supercon(archive_profile, details=details)
        archive_profile = SqliteZipBackend.create_profile(args.qe_file)
        load_visualize_phonon(archive_profile, details=details)

    else:
        print(
            "You must provide one of the following parameters: --file, --profile or --qe-file.",
            file=sys.stderr,
        )
        parser.print_help()
        sys.exit(1)

    for mc3d_id, detail in details.items():
        detail["phonons"] = find_finest_qdensity(detail["phonons"])

    check_base_json(details)
    with output_path.open("w") as handle:
        dump_canonical_json(details, handle)

    log("Done!")


if __name__ == "__main__":
    main()
