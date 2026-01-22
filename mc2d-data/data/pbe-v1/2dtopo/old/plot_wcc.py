import os
import re
import z2pack
import json

import matplotlib.pyplot as plt

wcc_setts = {
    "marker": "o",
    "facecolor": "none",
    "s": 10,
    "edgecolors": "k",
    "linewidth": 0.5,
}

gap_setts = {"marker": "o", "markersize": 8, "c": "r", "linewidth": 0}
root = "HWCC_plots/hwcc_json"
fname = "Bi2.json"


formula, _ = os.path.splitext(fname)
print(formula)
toprint = re.sub(r"(\d+)", r"$_{\1}$", formula)

fname = os.path.join(root, fname)
result = z2pack.io.load(fname)


def extract_z2_data(surface_result):
    """
    Mirror of z2pack.plot.wcc source code logic.
    Returns a dictionary instead of a matplotlib figure.
    """
    return {
        "k": list(surface_result.t),
        "gaps": [float(g % 1) for g in surface_result.gap_pos],
        "wcc": [[float(x % 1) for x in line.wcc] for line in surface_result.lines],
    }


minimal_data = extract_z2_data(result)

out_fname = "Bi2_.json"
with open(out_fname, "w") as f:
    json.dump(minimal_data, f)
