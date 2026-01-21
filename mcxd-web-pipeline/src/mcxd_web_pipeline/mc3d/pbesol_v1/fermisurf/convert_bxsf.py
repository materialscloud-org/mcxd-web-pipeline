#!/usr/bin/env python

import gzip
import shutil
import tempfile
from pathlib import Path

import convert_bxsf
import py7zr
from tqdm import tqdm

from mcxd_web_pipeline.config import CONFIG
from mcxd_web_pipeline.mc_mongo_injector import McMongoInjector
from mcxd_web_pipeline.s3_utils import upload_file_to_s3

BXSF_ARCHIVE_NAME = "bxsf.7z"
BXSF_FILE_NAME = "wjl.bxsf"

ENERGY_WINDOW = [-2, 2]  # eV
RESOLUTION = 20

FERMI_SURF_BASE_COLL = "pbesol-v1_fermisurf_base"


def get_bxsf_path_from_uuid(uuid, bxsf_root_path):
    """The path is sharded based on the 4 digits of the uuid"""
    part1 = uuid[:2]
    part2 = uuid[2:4]
    part3 = uuid[4:]
    return bxsf_root_path / part1 / part2 / part3 / BXSF_ARCHIVE_NAME


def extract_and_process(path: Path, mc3d_id: str, s3_prefix: str):
    """Extract the .7z to a temp folder, generate the json, gzip and upload."""
    if not path.exists():
        raise FileNotFoundError(path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with py7zr.SevenZipFile(path, mode="r") as z:
            z.extractall(path=tmpdir)

        bxsf_path = tmpdir / BXSF_FILE_NAME

        if not bxsf_path.exists():
            raise FileNotFoundError(f"{BXSF_FILE_NAME} was not found after extraction")

        json_path = tmpdir / f"{mc3d_id}.json"

        convert_bxsf.prepare_json(
            bxsf_path,
            energy_window=ENERGY_WINDOW,
            resolution=RESOLUTION,
            output_path=json_path,
        )

        gz_path = json_path.with_suffix(json_path.suffix + ".gz")
        with (
            json_path.open("rb") as f_in,
            gzip.open(gz_path, "wb", compresslevel=6) as f_out,
        ):
            shutil.copyfileobj(f_in, f_out)

        if not gz_path.exists():
            raise RuntimeError(f"Gzip step failed to produce: {gz_path}")

        s3_extras = {
            "ContentType": "application/json",
            "ContentEncoding": "gzip",
        }
        upload_file_to_s3(
            gz_path,
            CONFIG["s3"]["public_bucket"],
            f"{s3_prefix}/{mc3d_id}.json",
            s3_extras,
        )


def convert_and_upload_all():
    """
    Convert all BXSF files to json and upload to S3.
    # check at https://rgw.cscs.ch/matcloud:mc-discover-mcxd-public/mc3d/pbesol-v1_fermisurf/mc3d-55055.json
    """
    # Get the wannier calcjob UUIDs from MongoDB
    mmi = McMongoInjector(mcxd_type="mc3d")
    if FERMI_SURF_BASE_COLL not in mmi.db.list_collection_names():
        raise RuntimeError(f"Collection not found: {FERMI_SURF_BASE_COLL}")
    base_coll = mmi.db[FERMI_SURF_BASE_COLL]
    ids_and_wjl_uuids = list(base_coll.find({}, {"wannierjl_calcjob_uuid": 1}))

    bxsf_root_path = Path(
        CONFIG["info"]["mc3d"]["pbesol-v1-fermisurf"]["bxsf_root_path"]
    ).expanduser()

    s3_prefix = "mc3d/pbesol-v1_fermisurf/dev"

    print(
        f"Found {len(ids_and_wjl_uuids)} entries to process from MongoDB {FERMI_SURF_BASE_COLL}"
    )
    print(f"Finding corresponding BXSF files from {bxsf_root_path}")
    print(f"Converting and uploading to S3: {s3_prefix}")

    for entry in tqdm(ids_and_wjl_uuids):
        mcxd_id = entry["_id"]
        wjl_uuid = entry["wannierjl_calcjob_uuid"]

        path = get_bxsf_path_from_uuid(wjl_uuid, bxsf_root_path)
        extract_and_process(path, mcxd_id, s3_prefix)
