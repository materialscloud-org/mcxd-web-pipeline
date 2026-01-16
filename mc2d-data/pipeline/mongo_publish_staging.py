#!/usr/bin/env python
"""
Script to replace the production/ mongoDB collections with the staging/ ones.
"""

from pymongo import MongoClient

STAGING_PREFIX = "staging/"
OLD_PREFIX = "old/"

mongo_client = MongoClient("localhost", 27017)
mongo_db = mongo_client["mc2d"]

collections = mongo_db.list_collection_names()

staging_collections = [c for c in collections if c.startswith(STAGING_PREFIX)]

for staging_name in staging_collections:
    prod_name = staging_name.removeprefix(STAGING_PREFIX)
    print(f"Renaming {staging_name} -> {prod_name}")
    if prod_name in collections:
        old_name = OLD_PREFIX + prod_name
        print(f"    {prod_name} exists, renaming to {old_name}")
        mongo_db[prod_name].rename(old_name)
    mongo_db[staging_name].rename(prod_name)
