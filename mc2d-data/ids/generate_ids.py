#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate the list of IDs for the MC2D database.

Currently just assigns an MC2D-ID for each optimized 2d structure in the source metadata file.
Count starts from 1 and the original order is kept (which keep Mounet data first and Campi
extended data after).
"""

import json
import sys
from pathlib import Path

ID_FILE = Path("./mc2d-ids.json")
SOURCE_FILE = Path("../source-data/mc2d-data.json")

if ID_FILE.exists():
    print(f"{ID_FILE} already exists! adapt the script to allow extending it!")
    sys.exit(1)

with open(SOURCE_FILE) as fh:
    SOURCE_DATA = json.load(fh)

mc2d_ids = {}
id_counter = 1

for entry in SOURCE_DATA:
    opt_uuid = entry["optimized_2D_structure_uuid"]
    mc2d_ids[id_counter] = opt_uuid
    id_counter += 1

with ID_FILE.open("w") as fh:
    json.dump(mc2d_ids, fh, indent=2)
