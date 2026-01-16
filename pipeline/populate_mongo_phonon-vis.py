#!/usr/bin/env python
"""
Script to populate the "phonon-vis" contribution of the MC2D database.
"""

import json
import tarfile
from pathlib import Path

from pymongo import MongoClient

mongo_client = MongoClient("localhost", 27017)
mongo_db = mongo_client["mc2d"]

BASE_FOLDER = Path().resolve().parent / "data"
METHOD = "pbe-v1"
CONTRIB = "phonon-vis"

# first, we need to get the data from the out-phonons.tar.gz file
# and format it as a mapping of {mc2d_id -> phonon_vis_data}
# See README.md of the data folder for more information

TAR_FILE_PATH = BASE_FOLDER / METHOD / CONTRIB / "original-data" / "out-phonons.tar.gz"


def extract_tar_gz(file_path, extract_path):
    with tarfile.open(file_path, "r:gz") as tar:
        tar.extractall(path=extract_path)
        print(f"Extracted {file_path} to {extract_path}")


extract_path = TAR_FILE_PATH.parent
target_path = extract_path / "out-phonons"

if not target_path.exists():
    extract_tar_gz(TAR_FILE_PATH, extract_path)
else:
    print(f"skipping extraction, {str(target_path)} already exists.")

# the original data (out-phonons.tar.gz) contains
# * the phonon visualization json at the top level with chemical formula as the file name
# * uuids.json in a subfolder that we need to to match to a mc2d entry.
# let's make a mapping of {<phonon_bands_uuid> -> <phonon-visualization-data>}
phonon_vis_data = {}

for json_file in target_path.glob("*.json"):
    formula = json_file.stem

    with open(json_file) as fh:
        phonon_data = json.load(fh)

    uuids_json_file = target_path / formula / "uuids.json"
    with open(uuids_json_file) as fh:
        uuids_data = json.load(fh)

    phonon_vis_data[uuids_data["phonon_bands"]] = phonon_data

# To match this data to mc2d-ids, get the phonon_bands_uuids from base mc2d data

BASE_MC2D_DATA = BASE_FOLDER / METHOD / "base" / "base.json"

with open(BASE_MC2D_DATA) as fh:
    base_mc2d_data = json.load(fh)

# make a mapping of {<phonon_bands_uuid> -> <mc2d-id>}
phonon_mc2d_id_map = {}
for mc2d_id, entry in base_mc2d_data.items():
    phonon_bands_uuid = entry.get("vibrational", {}).get("phonon_bands_uuid")
    if phonon_bands_uuid:
        phonon_mc2d_id_map[phonon_bands_uuid] = mc2d_id

# inject the data to mongodb:

coll_name = f"staging/{METHOD}/{CONTRIB}"

if coll_name in mongo_db.list_collection_names():
    print(f"Collection {coll_name} exists, skipping data injection")
else:
    print(f"Injecting {coll_name}")
    for phonon_uuid, entry in phonon_vis_data.items():
        mc_id = phonon_mc2d_id_map[phonon_uuid]
        mongo_entry = {"_id": mc_id, **entry}
        mongo_db[coll_name].update_one({"_id": mc_id}, {"$set": entry}, upsert=True)
