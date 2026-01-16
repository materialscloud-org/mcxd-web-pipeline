#!/usr/bin/env python
"""
Script to populate the collections

* /overview
* /structure_uuids
"""

from pymongo import MongoClient

mongo_client = MongoClient("localhost", 27017)
mongo_db = mongo_client["mc2d"]

collections = mongo_db.list_collection_names()

METHOD = "pbe-v1"

STAGING_PREFIX = "staging/"


def populate_structure_uuids(method, coll_base):
    su_coll_name = f"{STAGING_PREFIX}{method}/structure-uuids"

    if su_coll_name in mongo_db.list_collection_names():
        print(f"Collection {su_coll_name} exists, skipping data injection")
    else:
        print(f"Injecting {su_coll_name}")
        for doc in coll_base.find():
            uuid = doc.get("general", {}).get("structure_relaxed_uuid", None)
            if uuid:
                entry = {"_id": doc["_id"], "uuid": uuid}
                mongo_db[su_coll_name].update_one(
                    {"_id": doc["_id"]}, {"$set": entry}, upsert=True
                )


def populate_overview_table(method, coll_base, metadata):
    index_coll_name = f"{STAGING_PREFIX}{method}/overview"

    if index_coll_name in mongo_db.list_collection_names():
        print(f"Collection {index_coll_name} exists, skipping data injection")
    else:
        print(f"Injecting {index_coll_name}")

        pipeline_project = {}

        for col in metadata["index-columns"]:
            if "array_index" in col:
                pipeline_project[col["data_label"]] = {
                    "$arrayElemAt": [f"${col['data_path']}", col["array_index"]]
                }
            else:
                pipeline_project[col["data_label"]] = f"${col['data_path']}"

        pipeline = [{"$project": pipeline_project}]

        results = list(coll_base.aggregate(pipeline))

        mongo_db[index_coll_name].insert_many(results)
        print(f"Inserted {len(results)} documents into '{index_coll_name}'")


cname_base = f"{STAGING_PREFIX}{METHOD}/base"
cname_meta = f"{STAGING_PREFIX}{METHOD}/meta"

if cname_base in collections and cname_meta in collections:
    coll_base = mongo_db[cname_base]
    metadata = mongo_db[cname_meta].find_one({"_id": "metadata"})

    populate_structure_uuids(METHOD, coll_base)
    populate_overview_table(METHOD, coll_base, metadata)
