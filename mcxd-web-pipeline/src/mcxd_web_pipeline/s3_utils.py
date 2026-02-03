#!/usr/bin/env python
"""
Tools to dump MongoDB collections to individual files and upload to S3.
"""

import os
import subprocess
from datetime import datetime

import boto3
from botocore.config import Config
from pymongo import MongoClient

S3_ENDPOINT_URL = os.environ["S3_ENDPOINT_URL"]
S3_ACCESS_KEY = os.environ["S3_ACCESS_KEY"]
S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]

S3_BUCKET = "mc-discover-mcxd"

LARGE_COLLECTIONS = {
    "mc3d": ["xrd", "supercon_phonon-vis"],
    "mc2d": [],
}

# keep s3 loaded in a global variable
_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
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
    return _s3_client


def upload_file_to_s3(file_path, s3_bucket, s3_key, extra_args={}):
    get_s3_client().upload_file(
        file_path, Bucket=s3_bucket, Key=s3_key, ExtraArgs=extra_args
    )


class MongoS3Uploader:
    def __init__(self, mongo_uri, mongo_db_name, mcxd_type):
        self.s3 = get_s3_client()

        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name

        self.mcxd_type = mcxd_type
        self.s3_prefix = f"{mcxd_type}-mongo-dumps/collections-v2/"

        # get all collection names
        client = MongoClient(self.mongo_uri)
        self.all_collections = client[self.mongo_db_name].list_collection_names()
        client.close()

    def _select_collections(self, method="all", selection="base"):
        """Select collections based on method and selection type.

        method: 'all', 'pbesol-v2', etc.
        selection: 'base' to get all the small base collections, or a large collection name
            to get only that large collection.
        """
        selected_collections = set()

        for coll in self.all_collections:
            method_ = coll.split("_")[0]

            if method != "all" and method_ != method:
                continue

            if selection == "all":
                # include all collections
                pass
            elif selection == "base":
                # skip large selections
                if any(ls in coll for ls in LARGE_COLLECTIONS[self.mcxd_type]):
                    continue
            elif selection in LARGE_COLLECTIONS[self.mcxd_type]:
                # for large selections, include only the selected ones
                if selection not in coll:
                    continue
            else:
                print(f"Unknown selection type: {selection}")
                return []
            selected_collections.add(coll)

        if selected_collections:
            # always upload the dataset-index
            selected_collections.add("dataset-index")
        return selected_collections

    def upload_collections(self, method="all", selection="base"):
        selected_collections = self._select_collections(method, selection)

        if not selected_collections:
            print("No collections matched the given selection. Exiting.")
            exit(1)

        print(f"Collections to dump: {', '.join(selected_collections)}")

        # === Timestamp & temp dir ===
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%SZ")
        tmp_dir = "/tmp/mcxd-mongo-collection-dumps"
        os.makedirs(tmp_dir, exist_ok=True)

        # === Dump & upload ===
        for coll in selected_collections:
            archive_name = f"{self.mcxd_type}-{coll}-dump-{timestamp}.archive.gz"
            local_archive_path = os.path.join(tmp_dir, archive_name)
            s3_key = f"{self.s3_prefix}{coll}/{archive_name}"

            print(f"Dumping collection: {coll}...")
            with open(local_archive_path, "wb") as f:
                subprocess.run(
                    [
                        "mongodump",
                        f"--uri={self.mongo_uri}",
                        f"--db={self.mongo_db_name}",
                        f"--collection={coll}",
                        "--archive",
                        "--gzip",
                    ],
                    check=True,
                    stdout=f,
                )

            print(f"Collection {coll} dump saved to {local_archive_path}")

            print(f"Uploading {coll} to s3://{S3_BUCKET}/{s3_key}...")
            self.s3.upload_file(local_archive_path, S3_BUCKET, s3_key)

            os.remove(local_archive_path)
            print(f"Upload complete for collection {coll} and temporary file removed.")

        print("All specified collections dumped and uploaded.")
