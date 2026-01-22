import matplotlib.pyplot as plt
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
test_file = os.path.join(SCRIPT_DIR, "../data/Bi2.json")


def plot_from_json(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    k = data["k"]
    gaps = data["gaps"]
    wcc_slices = data["wcc"]

    fig, ax = plt.subplots(figsize=(10, 6.2))

    # plot points in black.
    for ki, wcc_list in zip(k, wcc_slices):
        for offset in [-1, 0, 1]:
            ax.scatter(
                [ki] * len(wcc_list),
                [w + offset for w in wcc_list],
                s=10,
                facecolor="none",
                edgecolor="k",
                linewidth=0.5,
                zorder=2,
            )

    # plot gaps as red
    for offset in [-1, 0, 1]:
        ax.scatter(
            k,
            [g + offset for g in gaps],
            s=70,
            color="r",
            marker="o",
            linewidth=0,
            zorder=3,
        )

    # mpl formatting
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["0", r"$\pi/a$"], fontsize=18)
    ax.set_xlabel(r"$k$", fontsize=20)
    ax.set_ylabel(r"WCC $\overline{x}$", fontsize=20)

    plt.tight_layout()
    return fig


# plot and show
plot_from_json(test_file)
plt.show()
