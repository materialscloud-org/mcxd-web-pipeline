from pathlib import Path
from collections import defaultdict
from time import perf_counter
from typing import Any
from fnmatch import fnmatch
import argparse
import yaml
from pymongo import MongoClient

from aiida import load_profile
from aiida.orm import Node, QueryBuilder


# ============================================================
# Defaults
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_POLICY_FILE = BASE_DIR / "policy.yaml"
DEFAULT_MONGO_URI = "mongodb://localhost:27017"

UUID_SUFFIX = "_uuid"


# ============================================================
# CLI
# ============================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate MongoDB AiiDA UUID references."
    )

    parser.add_argument(
        "--policy",
        type=Path,
        default=DEFAULT_POLICY_FILE,
        help="Path to policy YAML file",
    )

    parser.add_argument(
        "--mongo-uri",
        default=DEFAULT_MONGO_URI,
        help="MongoDB connection URI",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--no-skips",
        action="store_true",
        help="Ignore skip_document_pairs policy entries",
    )

    return parser.parse_args()


# ============================================================
# Policy
# ============================================================


def load_policy(policy_file: Path):
    with open(policy_file, "r") as f:
        return yaml.safe_load(f)


# ============================================================
# UUID detection
# ============================================================


def is_aiida_uuid_field(key: str, value: Any) -> bool:
    return key.endswith(UUID_SUFFIX) and isinstance(value, str)


# ============================================================
# Policy helpers
# ============================================================


def skip_collection(policy, db, collection):
    return collection in policy.get("skip_collections", {}).get(db, [])


def allow_missing(policy, db, collection, path, doc_id, no_skips=False):
    if no_skips:
        return False

    return doc_id in policy.get("skip_document_pairs", {}).get(db, {}).get(
        collection, {}
    ).get(path, [])


def skip_path(policy, db, path):
    patterns = policy.get("skip_paths", {}).get(db, [])
    return any(fnmatch(path, p) for p in patterns)


# ============================================================
# Traversal
# ============================================================


def walk_document(obj: Any, path: str = ""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key

            if is_aiida_uuid_field(key, value):
                yield new_path, value

            if isinstance(value, (dict, list)):
                yield from walk_document(value, new_path)

    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                yield from walk_document(value, f"{path}[{idx}]")


# ============================================================
# Mongo extraction
# ============================================================


def extract_uuids_from_collection(collection, db, col, verbose=False):
    refs = []
    total_docs = 0
    total_refs = 0

    start = perf_counter()

    for doc in collection.find({}):
        total_docs += 1
        doc_id = str(doc["_id"])

        for path, uuid in walk_document(doc):
            refs.append(
                {
                    "database": db,
                    "collection": col,
                    "mongo_id": doc_id,
                    "path": path,
                    "uuid": uuid,
                }
            )
            total_refs += 1

    if verbose:
        print(
            f"[COLLECTION_DONE] {db}.{col} "
            f"docs={total_docs} refs={total_refs} "
            f"elapsed={perf_counter() - start:.2f}s"
        )

    return refs


# ============================================================
# AiiDA cache
# ============================================================


def load_profile_uuid_cache(profile_name: str):
    load_profile(profile_name, allow_switch=True)

    qb = QueryBuilder()
    qb.append(Node, project=["uuid"])

    return set(qb.all(flat=True))


def build_profile_uuid_caches(profiles, verbose=False):
    caches = {}

    for p in profiles:
        try:
            if verbose:
                print(f"[PROFILE] Loading {p}")

            caches[p] = load_profile_uuid_cache(p)

            if verbose:
                print(f"[PROFILE] Loaded {p} ({len(caches[p])} UUIDs)")

        except Exception as e:
            print(f"[PROFILE_LOAD_FAILED] {p}: {e}")

    return caches


# ============================================================
# Validation
# ============================================================


def validate_reference(
    ref,
    caches,
    policy,
    database_profiles,
    no_skips=False,
):
    db = ref["database"]
    col = ref["collection"]
    uuid = ref["uuid"]
    doc_id = ref["mongo_id"]
    path = ref["path"]

    if allow_missing(
        policy,
        db,
        col,
        path,
        doc_id,
        no_skips=no_skips,
    ):
        return None

    candidates = database_profiles[db]

    for profile in candidates:
        if profile in caches and uuid in caches[profile]:
            return None

    return {
        "type": "BROKEN_REF",
        "ref": ref,
    }


def validate_references(
    refs,
    caches,
    policy,
    database_profiles,
    no_skips=False,
):
    failures = []

    for r in refs:
        res = validate_reference(
            r,
            caches,
            policy,
            database_profiles,
            no_skips=no_skips,
        )

        if res:
            failures.append(res)

    return failures


# ============================================================
# Main
# ============================================================


def run():
    args = parse_args()

    policy = load_policy(args.policy)
    database_profiles = policy["database_profiles"]

    client = MongoClient(args.mongo_uri)

    all_profiles = {p for v in database_profiles.values() for p in v}

    print("Loading AiiDA caches...")

    caches = build_profile_uuid_caches(
        all_profiles,
        verbose=args.verbose,
    )

    all_failures = []

    for db in database_profiles:
        print(f"\n[DATABASE] {db}")

        for col in client[db].list_collection_names():
            if skip_collection(policy, db, col):
                if args.verbose:
                    print(f"[SKIP_COLLECTION] {db}.{col}")
                continue

            refs = extract_uuids_from_collection(
                client[db][col],
                db,
                col,
                verbose=args.verbose,
            )

            failures = validate_references(
                refs,
                caches,
                policy,
                database_profiles,
                no_skips=args.no_skips,
            )

            all_failures.extend(failures)

    print()
    print("=" * 80)
    print(f"TOTAL FAILURES: {len(all_failures)}")
    print("=" * 80)

    if all_failures:
        for failure in all_failures:
            ref = failure["ref"]

            print(
                f"{ref['database']}.{ref['collection']} "
                f"doc={ref['mongo_id']} "
                f"path={ref['path']} "
                f"uuid={ref['uuid']}"
            )

    return all_failures


# ============================================================
# Entrypoint
# ============================================================


if __name__ == "__main__":
    failures = run()

    if failures:
        raise SystemExit(1)
