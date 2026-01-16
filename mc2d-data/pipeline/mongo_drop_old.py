#!/usr/bin/env python
"""
Script to replace the production/ mongoDB collections with the staging/ ones.
"""

from pymongo import MongoClient

OLD_PREFIX = "old/"

mongo_client = MongoClient("localhost", 27017)
mongo_db = mongo_client["mc2d"]

collections = mongo_db.list_collection_names()

for coll in collections:
    if coll.startswith(OLD_PREFIX):
        mongo_db[coll].drop()
        print(f"Dropped {coll}")
