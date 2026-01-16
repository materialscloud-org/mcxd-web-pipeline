import json
import os
import time
from functools import lru_cache

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")

_mongo_client = None


def get_mongo_client():
    """Get or create MongoDB client singleton"""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(
            MONGODB_URI,
            socketTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _mongo_client


@lru_cache(maxsize=32)
def _cached_collections_with_timestamp(
    db_name: str, timestamp_bucket: int
) -> frozenset:
    """Internal function that includes timestamp in cache key for TTL behavior"""
    mongo_client = get_mongo_client()
    return frozenset(mongo_client[db_name].list_collection_names())


def cached_collections(db_name: str) -> frozenset:
    """Get cached collections with 1-minute TTL"""
    current_time = int(time.time())
    timestamp_bucket = current_time // 60
    return _cached_collections_with_timestamp(db_name, timestamp_bucket)


def validate_and_return_collection(db_name, collection_name):
    if collection_name not in cached_collections(db_name):
        raise HTTPException(
            status_code=404, detail=f"Collection {collection_name} not found!"
        )
    mongo_client = get_mongo_client()
    return mongo_client[db_name][collection_name]


def return_all_mongodb_entries(db_name, collection_name):
    coll = validate_and_return_collection(db_name, collection_name)
    pipeline = [
        {"$addFields": {"id": "$_id"}},
        {"$project": {"_id": 0}},
    ]
    results = list(coll.aggregate(pipeline))
    return results


def return_one_mongodb_entry(db_name, collection_name, entry_id):
    coll = validate_and_return_collection(db_name, collection_name)
    entry = coll.find_one({"_id": entry_id})
    if entry:
        entry["id"] = entry.pop("_id")
        return JSONResponse(entry)
    else:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")


@lru_cache(maxsize=32)
def _get_cached_data_with_timestamp(
    db_name: str, collection_name: str, timestamp_bucket: int
) -> str:
    """Internal function that includes timestamp in cache key for TTL behavior"""
    results = return_all_mongodb_entries(db_name, collection_name)
    return json.dumps(results)


def get_cached_data(db_name: str, collection_name: str, ttl: int = 600) -> str:
    """Get cached overview with 10-minute TTL"""
    current_time = int(time.time())
    timestamp_bucket = current_time // ttl
    return _get_cached_data_with_timestamp(db_name, collection_name, timestamp_bucket)
