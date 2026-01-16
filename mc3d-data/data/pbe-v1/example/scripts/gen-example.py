#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script that generates example data.
"""

import json
from pathlib import Path

BASE_DATA_PATH = Path(__file__).parent.parent.parent / "base"

with (BASE_DATA_PATH / "data.json").open("r") as handle:
    base_data = json.load(handle)

OUTPUT_PATH = Path(__file__).parent.parent

details = {}

for id, entry in base_data.items():
    # count capital letters in formula to get the number of elements
    num_elements = sum(1 for c in entry["general"]["formula"] if c.isupper())

    details[id] = {"example": {"num_elements": num_elements}}

with (OUTPUT_PATH / "data.json").open("w") as handle:
    json.dump(details, handle, sort_keys=True, indent=2)
