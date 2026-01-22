import os
import re
import z2pack
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

original_json_root = os.path.join(SCRIPT_DIR, "../original_data/hwcc_json")
output_json_root = os.path.join(SCRIPT_DIR, "../data/hwcc_json")

for fname in os.listdir(original_json_root):
    if not fname.endswith("json"):
        continue

    formula, _ = os.path.splitext(fname)
    toprint = re.sub(r"(\d+)", r"$_{\1}$", formula)

    fname = os.path.join(original_json_root, fname)
    result = z2pack.io.load(fname)

    def extract_z2_data(surface_result):
        """
        Mirror of z2pack.plot.wcc source code logic, but returns formatted data.
        """
        return {
            "k": list(surface_result.t),
            "gaps": [round(float(g % 1), 4) for g in surface_result.gap_pos],
            "wcc": [
                [round(float(x % 1), 4) for x in line.wcc]
                for line in surface_result.lines
            ],
        }

    minimal_data = extract_z2_data(result)

    out_fname = f"{formula}.json"

    with open(f"{output_json_root}/{out_fname}", "w") as f:
        json.dump(minimal_data, f)
