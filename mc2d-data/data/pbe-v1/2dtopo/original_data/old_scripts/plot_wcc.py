import os
import re
import z2pack

import matplotlib.pyplot as plt

wcc_setts = {
    "marker": "o",
    "facecolor": "none",
    "s": 10,
    "edgecolors": "k",
    "linewidth": 0.5,
}
gap_setts = {"marker": "o", "markersize": 8, "c": "r", "linewidth": 0}
root = "hwcc_json"
for fname in os.listdir(root):
    if not fname.endswith("json"):
        continue
    formula, _ = os.path.splitext(fname)
    print(formula)
    toprint = re.sub(r"(\d+)", r"$_{\1}$", formula)

    fname = os.path.join(root, fname)
    result = z2pack.io.load(fname)

    fig, ax = plt.subplots(figsize=(10, 6.2))
    # ax.set_title(f'{toprint}')
    z2pack.plot.wcc(result, axis=ax, wcc_settings=wcc_setts, gap_settings=gap_setts)

    ax.xaxis.set_label_text(r"$k$", fontsize=22)
    ax.xaxis.set_ticks([0, 1])
    ax.xaxis.set_ticklabels(["0", r"$\pi / a$"], fontsize=20)

    ax.yaxis.set_label_text(r"$\overline{x}$", fontsize=22)
    ax.yaxis.set_tick_params(labelsize=20)

    plt.savefig(f"wcc_{formula}.png")
    plt.savefig(f"pdf/wcc_{formula}.pdf")
    # plt.show()
    # break
