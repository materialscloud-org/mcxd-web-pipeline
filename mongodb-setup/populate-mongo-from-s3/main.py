#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import boto3
from botocore.config import Config
from pymongo import MongoClient, errors

S3_ENDPOINT_URL = os.environ["S3_ENDPOINT_URL"]
S3_ACCESS_KEY = os.environ["S3_ACCESS_KEY"]
S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]

S3_BUCKET = os.environ["S3_BUCKET"]
S3_PREFIX = os.environ["S3_PREFIX"]

TARGET_DB = S3_PREFIX.split("-")[0]

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")


def wait_for_mongodb(uri, max_retries=10, retry_interval=5):
    for i in range(max_retries):
        try:
            print(f"Attempt {i + 1}: Connecting to MongoDB at {uri}...")
            client = MongoClient(uri, tz_aware=False)
            client.admin.command("ping")
            return client
        except (
            errors.ConnectionFailure,
            errors.ServerSelectionTimeoutError,
            errors.AutoReconnect,
            errors.NetworkTimeout,
            errors.OperationFailure,
        ) as e:
            print(f"MongoDB error: {e}")
            time.sleep(retry_interval)
    else:
        raise RuntimeError("MongoDB did not become ready in time.")


def decompress_if_needed(src_path: Path, dst_path: Path) -> Path:
    """
    Ensure we have an uncompressed .archive file.
    If src is .gz, decompress (prefer pigz, else Python gzip).
    Returns path to uncompressed archive.
    """
    if src_path.suffix == ".gz":
        print(f"Decompressing {src_path.name} -> {dst_path.name}")
        if shutil.which("pigz") is not None:
            # pigz is ~multi-core gzip; much faster than gunzip
            subprocess.run(
                ["pigz", "-d", "-c", str(src_path)],
                check=True,
                stdout=open(dst_path, "wb"),
            )
        else:
            with gzip.open(src_path, "rb") as f_in, open(dst_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return dst_path
    else:
        # Already uncompressed .archive
        if src_path != dst_path:
            shutil.copyfile(src_path, dst_path)
        return dst_path


mongo_client = wait_for_mongodb(MONGODB_URI)
restore_log = mongo_client["admin"][f"{TARGET_DB}_restore_log"]

# Check if mongorestore is available
if not shutil.which("mongorestore"):
    print("Error: 'mongorestore' is not installed or not in PATH.")
    sys.exit(1)

# Create the S3 client
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)

# === 1. List all objects ===
print(f"Listing S3 objects in s3://{S3_BUCKET}/{S3_PREFIX}")
objects = []
continuation_token = None
while True:
    kwargs = {"Bucket": S3_BUCKET, "Prefix": S3_PREFIX}
    if continuation_token:
        kwargs["ContinuationToken"] = continuation_token
    resp = s3.list_objects_v2(**kwargs)
    objects.extend(resp.get("Contents", []))
    if not resp.get("IsTruncated"):
        break
    continuation_token = resp.get("NextContinuationToken")

if not objects:
    print("No dump files found. Exiting.")
    sys.exit(1)

# === 2. Group by collection & pick latest file ===
latest_files = {}
for obj in objects:
    key = obj["Key"]
    if not (key.endswith(".archive.gz") or key.endswith(".archive")):
        continue
    parts = key[len(S3_PREFIX) :].split("/")
    if len(parts) != 2:
        continue
    coll, filename = parts
    # choose newest by filename (assumes your timestamp in name is lexicographically sortable; ISO-ish is OK)
    if coll not in latest_files or filename > latest_files[coll]["filename"]:
        latest_files[coll] = {"key": key, "filename": filename}


if not latest_files:
    print("No valid collection dumps found.")
    sys.exit(1)

print("Latest dumps to restore (skipping already restored):")

# === 3. Download & restore each ===
try:
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        for coll, data in latest_files.items():
            # Skip if already restored
            if restore_log.find_one({"s3_key": data["key"], "restored": True}):
                print(f"Skipping {coll}: {data['key']} (already restored)")
                continue

            dl_name = f"{coll}.archive"
            gzip = False
            if data["key"].endswith(".gz"):
                dl_name += ".gz"
                gzip = True

            dl_path = base_path / dl_name
            print(f"Downloading s3://{S3_BUCKET}/{data['key']} to {dl_path}")
            s3.download_file(S3_BUCKET, data["key"], dl_path)

            archive_path = base_path / f"{coll}.archive"
            decompress_if_needed(dl_path, archive_path)

            cmd = [
                "mongorestore",
                "--uri",
                MONGODB_URI,
                f"--archive={archive_path}",
                "--drop",
                # to speed up restoring:
                "--numInsertionWorkersPerCollection=2",
                '--writeConcern={"w":1,"j":false}',
            ]

            print(f"Restoring collection {coll}...")
            subprocess.run(cmd, check=True)
            print(f"Collection {coll} restored.")

            # Mark as restored
            restore_log.update_one(
                {"s3_key": data["key"]},
                {"$set": {"s3_key": data["key"], "restored": True}},
                upsert=True,
            )

    print("All new collections restored successfully.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
