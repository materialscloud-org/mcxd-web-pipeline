#!/usr/bin/env python

import brotli
import shutil
import tempfile
from pathlib import Path

import py7zr
from tqdm import tqdm

from mcxd_web_pipeline.config import CONFIG
from mcxd_web_pipeline.mc_mongo_injector import McMongoInjector
from mcxd_web_pipeline.s3_utils import upload_file_to_s3

### Method for uploading cube files to S3
### Wannier data has an archive file
WANN_ARCHIVE_NAME = "wan_tb_cube.7z"

# which when unzipped becomes a folder with N .cube files.
# there also seems to be a very large aiida_tb.dat file...?
extension = ".cube"

WANNIER_BASE_COLL = "pbesol-v1_wannierisation_base"


def get_path_from_uuid(uuid, wannier_root_path):
    """The path is sharded based on the 4 digits of the uuid"""
    part1 = uuid[:2]
    part2 = uuid[2:4]
    part3 = uuid[4:]
    return wannier_root_path / part1 / part2 / part3 / WANN_ARCHIVE_NAME


def extract_and_upload_cubes(
    path: Path,
    mc3d_id: str,
    s3_prefix: str,
    compressionlevel: int = 11,
):
    """Extract the .7z archive, compress each .cube file with Brotli,
    and upload to S3, preserving filenames."""

    if not path.exists():
        raise FileNotFoundError(path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Extract all files from archive
        with py7zr.SevenZipFile(path, mode="r") as z:
            z.extractall(path=tmpdir)

        # Find all .cube files recursively
        cube_files = list(tmpdir.rglob("*.cube"))
        if not cube_files:
            raise FileNotFoundError("No .cube files found in the archive")

        for cube_path in cube_files:
            # Compress with Brotli
            br_path = cube_path.with_suffix(cube_path.suffix + ".br")
            with cube_path.open("rb") as f_in:
                compressed_data = brotli.compress(f_in.read(), quality=compressionlevel)
            with br_path.open("wb") as f_out:
                f_out.write(compressed_data)

            if not br_path.exists():
                raise RuntimeError(f"Brotli step failed for: {br_path}")

            # Upload to S3
            s3_extras = {
                "ContentType": "application/octet-stream",
                "ContentEncoding": "br",
            }

            # Preserve relative path inside archive for S3
            relative_path = br_path.relative_to(tmpdir)
            s3_key = f"{s3_prefix}/{mc3d_id}/{relative_path}"

            upload_file_to_s3(
                br_path,
                CONFIG["s3"]["public_bucket"],
                s3_key,
                s3_extras,
            )


def convert_and_upload_all():
    """
    Convert all wannier cube files to json and upload to S3.
    # check at https://rgw.cscs.ch/matcloud:mc-discover-mcxd-public/mc3d/pbesol-v1_wannierisation/mc3d-73573.json
    """
    # Get the calcjob UUIDs from MongoDB
    mmi = McMongoInjector(mcxd_type="mc3d")
    if WANNIER_BASE_COLL not in mmi.db.list_collection_names():
        raise RuntimeError(f"Collection not found: {WANNIER_BASE_COLL}")
    base_coll = mmi.db[WANNIER_BASE_COLL]
    ids_and_wjl_uuids = list(base_coll.find({}, {"cj_stash_uuid": 1}))

    wannier_root_path = Path(
        CONFIG["info"]["mc3d"]["pbesol-v1-wannierisation"]["wannier_root_path"]
    ).expanduser()

    s3_prefix = "mc3d/pbesol-v1_wannierisation/dev"

    print(
        f"Found {len(ids_and_wjl_uuids)} entries to process from MongoDB {WANNIER_BASE_COLL}"
    )
    print(f"Finding corresponding cube files files from {wannier_root_path}")
    print(f"Converting and uploading to S3: {s3_prefix}")

    for entry in tqdm(ids_and_wjl_uuids):
        mcxd_id = entry["_id"]
        wjl_uuid = entry["cj_stash_uuid"]

        path = get_path_from_uuid(wjl_uuid, wannier_root_path)
        extract_and_upload_cubes(path, mcxd_id, s3_prefix)
