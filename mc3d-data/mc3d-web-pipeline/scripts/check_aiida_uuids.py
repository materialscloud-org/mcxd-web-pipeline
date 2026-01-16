#!/usr/bin/env python3
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Set, Tuple
from uuid import UUID

UUID_REGEX = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)

PathType = Tuple[Any, ...]  # sequence of keys/indices leading to the value


def format_path(path: PathType) -> str:
    """Format a path like ('root', 'level1', 2, 'leaf') -> root.level1[2].leaf"""
    parts: List[str] = []
    for p in path:
        if isinstance(p, int):
            parts[-1] = f"{parts[-1]}[{p}]"
        else:
            parts.append(str(p))
    return ".".join(parts) if parts else "$"


def merge_into(dest: DefaultDict[str, Set[PathType]], src: Dict[str, Set[PathType]]):
    """Union path sets from src into dest."""
    for k, v in src.items():
        dest[k] |= v


def find_uuids_with_paths(obj: Any, path: PathType = ()) -> Dict[str, Set[PathType]]:
    """
    Recursively find UUIDs in JSON-like structure **values only**.
    Returns a dict: uuid -> set of paths where it appears.
    """
    found: DefaultDict[str, Set[PathType]] = defaultdict(set)

    if isinstance(obj, dict):
        for k, v in obj.items():
            # do not scan 'k' itself; we only scan values
            merge_into(found, find_uuids_with_paths(v, path + (k,)))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            merge_into(found, find_uuids_with_paths(item, path + (i,)))
    elif isinstance(obj, str):
        for raw in UUID_REGEX.findall(obj):
            try:
                u = str(UUID(raw))  # validate & normalize (lowercase)
                found[u].add(path)
            except Exception:
                pass
    # other scalar types ignored
    return found


# ---------- Local profile mode ----------
def batch_check_nodes_profile(uuids: Set[str]) -> Set[str]:
    """Return the subset of UUIDs that exist as Nodes in a local AiiDA profile."""
    if not uuids:
        return set()
    from aiida.orm import Node, QueryBuilder  # lazy import

    qb = QueryBuilder()
    qb.append(Node, filters={"uuid": {"in": list(uuids)}}, project=["uuid"])
    return {row[0] if isinstance(row, (list, tuple)) else row for row in qb.all()}


# ---------- REST mode ----------
def ensure_nodes_url(s: str) -> str:
    """
    Normalize REST base to .../api/v4/nodes (no trailing slash).
    Accepts:
      - dataset root: https://host/path/project
      - .../api/v4
      - .../api/v4/
      - .../api/v4/nodes
      - .../api/v4/nodes/
      - .../api/v4/nodes/<uuid>
    Always returns: https://.../api/v4/nodes
    """
    url = s.strip().rstrip("/")
    lower = url.lower()

    # Already contains /api/v4/nodes -> trim after /nodes
    if "/api/v4/nodes" in lower:
        idx = lower.find("/api/v4/nodes")
        return url[: idx + len("/api/v4/nodes")]

    # Has /api/v4 -> append /nodes
    if "/api/v4" in lower:
        idx = lower.find("/api/v4")
        base = url[: idx + len("/api/v4")]
        return base + "/nodes"

    # Has some /api/vX -> replace with /api/v4/nodes
    if "/api/v" in lower:
        pre = url[: lower.find("/api/v")]
        return pre + "/api/v4/nodes"

    # No api segment -> append /api/v4/nodes
    return url + "/api/v4/nodes"


def check_rest_exists(nodes_base: str, uuid: str, timeout: float) -> bool:
    """Return True if GET <nodes_base>/<uuid> returns a 2xx status, else False."""
    import requests  # lazy import to avoid dependency if only using profile mode

    url = f"{nodes_base}/{uuid}"
    try:
        r = requests.get(
            url,
            headers={"Accept": "application/json"},
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        r.close()
        return 200 <= r.status_code < 300
    except Exception:
        return False


def batch_check_nodes_rest(
    uuids: Set[str], nodes_base: str, timeout: float = 10.0, jobs: int = 8
) -> Set[str]:
    """Return the subset of UUIDs that exist at the REST endpoint."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    found: Set[str] = set()
    if not uuids:
        return found

    def worker(u: str):
        return u if check_rest_exists(nodes_base, u, timeout) else None

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        futures = {ex.submit(worker, u): u for u in uuids}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                found.add(res)
    return found


def main():
    p = argparse.ArgumentParser(
        description="Check AiiDA Node UUIDs in a JSON file (values only), via local profile or REST API."
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--profile", help="AiiDA profile name")
    mode.add_argument(
        "--rest",
        help=(
            "Dataset base URL (the script will use '<URL>/api/v4/nodes'), e.g.: "
            "https://aiida.dev.materialscloud.org/mc3d-pbesol-v1-supercon"
        ),
    )
    p.add_argument("json_file", type=Path, help="Path to JSON file")
    p.add_argument("--timeout", type=float, default=10.0, help="REST timeout (s)")
    p.add_argument(
        "--jobs", type=int, default=8, help="Parallel requests for REST mode"
    )
    args = p.parse_args()

    # Load JSON file
    try:
        data = json.loads(args.json_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(
            f"[ERROR] Failed to read/parse JSON file '{args.json_file}': {e}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Extract UUIDs from values and remember paths
    uuid_paths = find_uuids_with_paths(data, path=("root",))
    all_uuids = set(uuid_paths.keys())

    if not all_uuids:
        print("No valid UUIDs found in JSON values.")
        sys.exit(0)

    if args.profile:
        print(
            f"Found {len(all_uuids)} UUID(s) in values. "
            f"Checking Nodes via local profile '{args.profile}'..."
        )
        try:
            from aiida.manage.configuration import load_profile  # lazy import

            load_profile(args.profile)
        except Exception as e:
            print(
                f"[ERROR] Failed to load AiiDA profile '{args.profile}': {e}",
                file=sys.stderr,
            )
            sys.exit(2)
        present = batch_check_nodes_profile(all_uuids)
    else:
        nodes_base = ensure_nodes_url(args.rest)
        print(
            f"Found {len(all_uuids)} UUID(s) in values. "
            f"Checking Nodes via REST at '{nodes_base}/<uuid>' "
            f"(timeout={args.timeout}s, jobs={args.jobs})..."
        )
        present = batch_check_nodes_rest(
            all_uuids, nodes_base, timeout=args.timeout, jobs=args.jobs
        )

    missing = sorted(all_uuids - present)

    # Only print missing UUIDs with their paths
    for u in missing:
        print(f"{u}: NOT FOUND")
        for p in sorted(uuid_paths[u], key=format_path):
            print(f"  at: {format_path(p)}")

    # Summary + exit code useful for CI
    print("\nSummary:")
    print(f"  Present in Nodes: {len(present)}")
    print(f"  Missing in Nodes: {len(missing)}")

    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
