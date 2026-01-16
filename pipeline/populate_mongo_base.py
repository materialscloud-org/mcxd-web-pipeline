#!/usr/bin/env python
"""
Script to populate the "base" of the MC2D database.

This includes the base contributions, but also any supplementary
contributions that directly contribute to the base endpoints.
"""

import json
from pathlib import Path

from pymongo import MongoClient

mongo_client = MongoClient("localhost", 27017)
mongo_db = mongo_client["mc2d"]

BASE_FOLDER = Path().resolve().parent / "data"
METHOD = "pbe-v1"


def inject_base_meta(coll_name, contrib_path):
    """Inject the base/meta.json data into its collection."""
    if coll_name in mongo_db.list_collection_names():
        print(f"Collection {coll_name} exists, skipping data injection")
    else:
        print(f"Injecting {coll_name}")
        with (contrib_path / "meta.json").open("r") as fhandle:
            meta = json.load(fhandle)
        # metadata will be a single document in the meta collection
        mongo_db[coll_name].update_one({"_id": "metadata"}, {"$set": meta}, upsert=True)


def inject_base_data(coll_name, contrib_path):
    """Inject the base/data.json data into its collection."""
    if coll_name in mongo_db.list_collection_names():
        print(f"Collection {coll_name} exists, skipping data injection")
    else:
        print(f"Injecting {coll_name}")
        with (contrib_path / "base.json").open("r") as fhandle:
            details = json.load(fhandle)
        for mc_id, val in details.items():
            entry = {"_id": mc_id, **val}
            # Add or update if already exists
            mongo_db[coll_name].update_one({"_id": mc_id}, {"$set": entry}, upsert=True)


method_path = BASE_FOLDER / METHOD

coll_name_base = f"staging/{METHOD}/base"
coll_name_meta = f"staging/{METHOD}/meta"

inject_base_meta(coll_name_meta, method_path / "base")
inject_base_data(coll_name_base, method_path / "base")
