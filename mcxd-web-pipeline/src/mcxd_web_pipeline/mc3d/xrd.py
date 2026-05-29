from aiida import load_profile
from aiida import orm

import numpy as np
from tqdm import tqdm

import pymatgen.analysis.diffraction.xrd as xrd
import json
import brotli

import tempfile

from mcxd_web_pipeline.config import CONFIG
from pathlib import Path

from mcxd_web_pipeline.s3_utils import upload_file_to_s3, get_s3_client
from mcxd_web_pipeline.mc_mongo_injector import McMongoInjector

from concurrent.futures import ProcessPoolExecutor, as_completed
import os


NUM_CORES = max(1, os.cpu_count() - 4)


def calc_pattern_test(pmg_struct, wavelength="CuKa", two_th_range=(0, 90)):
    """
    Calculate powder xray diffraction pattern for a given structure using pymatgen XRDCalculator.
    """
    xrd_calc = xrd.XRDCalculator(wavelength)
    pattern = xrd_calc.get_pattern(pmg_struct, two_theta_range=two_th_range)
    return pattern


def run_and_upload_one_xrd(
    mc3d_id,
    structure_uuid,
    s3_prefix,
    wavelengths=("CuKa", "MoKa", "CrKa", "FeKa", "CoKa", "AgKa"),
    compressionlevel: int = 11,
):
    sd_node = orm.load_node(structure_uuid)
    pmg_structure = sd_node.get_pymatgen_structure()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        files = []

        # ---- STEP 1: compute + write locally ----
        for wavelength in wavelengths:
            pattern = calc_pattern_test(pmg_structure, wavelength)

            xrd_data = {
                "wavelength": wavelength,
                "angular_range": (0, 90),
                "peaks_positions": np.around(pattern.x, 4).tolist(),
                "intensities": np.around(pattern.y, 4).tolist(),
                "hkls": [h[0]["hkl"] for h in pattern.hkls],
            }

            raw = json.dumps(
                xrd_data, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            compressed = brotli.compress(raw, quality=compressionlevel)

            out_file = tmpdir / f"{wavelength}.json.br"
            out_file.write_bytes(compressed)

            files.append((wavelength, out_file))

        # ---- STEP 2: upload ----
        for wavelength, file_path in files:
            s3_key = f"{s3_prefix}/{mc3d_id}/{wavelength}.json.br"

            upload_file_to_s3(
                file_path,
                CONFIG["s3"]["public_bucket"],
                s3_key,
                {
                    "ContentType": "application/json",
                    "ContentEncoding": "br",
                },
            )


def s3_object_exists(bucket, key):
    client = get_s3_client()

    try:
        client.head_object(
            Bucket=bucket,
            Key=key,
        )
        return True

    except Exception as e:
        error_code = e.response["Error"]["Code"]

        if error_code in ("404", "NoSuchKey"):
            return False

        raise


def _worker(entry, s3_prefix, skip=True):
    mc3d_id = entry["_id"]
    structure_uuid = entry["uuid"]

    sentinel_key = f"{s3_prefix}/{mc3d_id}/AgKa.json.br"

    if skip == True:
        if s3_object_exists(
            CONFIG["s3"]["public_bucket"],
            sentinel_key,
        ):
            return

    run_and_upload_one_xrd(
        mc3d_id=mc3d_id,
        structure_uuid=structure_uuid,
        s3_prefix=s3_prefix,
    )

    return mc3d_id


def convert_and_upload_all(database, skip=True):
    """
    Parallelized XRD generation + S3 upload.
    """

    mmi = McMongoInjector(mcxd_type="mc3d")
    BASE_COLL = f"{database}_core_structure-uuids"
    base_coll = mmi.db[BASE_COLL]

    entries = list(base_coll.find({}, {"_id": 1, "uuid": 1}))

    s3_prefix = f"mc3d/{database}_xrd/dev"

    print(f"Found {len(entries)} entries")
    print(f"Uploading to S3: {s3_prefix}")
    print(f"Using {NUM_CORES} processes")

    with ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
        futures = {
            executor.submit(_worker, entry, s3_prefix, skip=skip): entry["_id"]
            for entry in entries
        }

        for future in tqdm(as_completed(futures), total=len(futures)):
            mc3d_id = futures[future]

            try:
                future.result()
            except Exception as e:
                print(f"[FAIL] {mc3d_id}: {e}")


def populate_xrd_s3(method, skip):
    load_profile(f"mc3d-{method}")
    convert_and_upload_all(method, skip)
