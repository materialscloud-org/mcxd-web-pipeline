#!/usr/bin/env python
"""
Script to dump MongoDB collections (explicit names or glob patterns) to individual files and upload to S3.
Collections can be specified by CLI argument or environment variable.
"""

import os
import subprocess
import sys
from datetime import datetime
from fnmatch import fnmatch

import boto3
from botocore.config import Config
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "mc3d"

COLLECTIONS = None
if len(sys.argv) > 1:
    COLLECTIONS = sys.argv[1:]
elif os.environ.get("COLLECTIONS"):
    COLLECTIONS = os.environ.get("COLLECTIONS").split()

if COLLECTIONS is None:
    print("No collections specified, exiting.")
    print("To dump all collections, use 'all'.")
    sys.exit(1)

S3_ENDPOINT_URL = os.environ["S3_ENDPOINT_URL"]
S3_ACCESS_KEY = os.environ["S3_ACCESS_KEY"]
S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]

S3_BUCKET = "mc-discover-mcxd"
S3_PREFIX = f"{DB_NAME}-mongo-dumps/collections/"

# Create the S3 client
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    # Needed to prevent XAmzContentSHA256Mismatch on upload:
    config=Config(
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)

# === Timestamp & temp dir ===
timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%SZ")
tmp_dir = "/tmp/mongo-collection-dumps"
os.makedirs(tmp_dir, exist_ok=True)

# === Get all collection names ===
client = MongoClient(MONGO_URI)
all_collections = client[DB_NAME].list_collection_names()
client.close()

print(all_collections)

# === Resolve patterns ===
resolved_collections = set()
for pattern in COLLECTIONS:
    if pattern == "all":
        resolved_collections.update(all_collections)
        break
    for coll in all_collections:
        if fnmatch(coll, pattern):
            resolved_collections.add(coll)
resolved_collections = sorted(resolved_collections)

if not resolved_collections:
    print("No collections matched the given patterns. Exiting.")
    exit(1)

print(f"Collections to dump: {', '.join(resolved_collections)}")

# === Dump & upload ===
for coll in resolved_collections:
    coll_sanitized = coll.replace("/", "_")
    archive_name = f"{DB_NAME}-{coll_sanitized}-dump-{timestamp}.archive.gz"
    local_archive_path = os.path.join(tmp_dir, archive_name)
    s3_key = f"{S3_PREFIX}{coll_sanitized}/{archive_name}"

    print(f"Dumping collection: {coll}...")
    with open(local_archive_path, "wb") as f:
        subprocess.run(
            [
                "mongodump",
                f"--uri={MONGO_URI}",
                f"--db={DB_NAME}",
                f"--collection={coll}",
                "--archive",
                "--gzip",
            ],
            check=True,
            stdout=f,
        )

    print(f"Collection {coll} dump saved to {local_archive_path}")

    print(f"Uploading {coll} to s3://{S3_BUCKET}/{s3_key}...")
    s3.upload_file(local_archive_path, S3_BUCKET, s3_key)

    os.remove(local_archive_path)
    print(f"Upload complete for collection {coll} and temporary file removed.")

print("All specified collections dumped and uploaded.")
