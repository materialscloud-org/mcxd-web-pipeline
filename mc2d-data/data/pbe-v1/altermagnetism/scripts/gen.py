#!/usr/bin/env python3
"""Regenerate base.json from the supplied results export (Python standard library)."""
import argparse
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def generate(source):
    rows = json.loads(source.read_text())
    if not isinstance(rows, list):
        raise ValueError("Source must be a list")
    result = {}
    for row in rows:
        item = dict(row)
        key = item.pop("mc2d-ID")
        if not re.fullmatch(r"mc2d-[0-9]+", key):
            raise ValueError(f"Invalid ID: {key}")
        if key in result:
            raise ValueError(f"Duplicate ID: {key}")
        for field in ("altermagnets_workchain_uuid", "pw_bands_workchain_uuid"):
            if item[field] == "NA":
                item[field] = None
        item["citations"] = ["Bose2026"]
        result[key] = item
    return result
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "original_data/altermagnets_data.json")
    parser.add_argument("--output", type=Path, default=ROOT / "base.json")
    args = parser.parse_args()
    result = generate(args.source)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Generated {len(result)} records: {args.output}")
