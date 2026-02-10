import json
from collections import defaultdict
import matplotlib.pyplot as plt
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

VERIFICATION_FOLDER = os.path.join(SCRIPT_DIR, "../verification")
REPORT_FILE = os.path.join(VERIFICATION_FOLDER, "method_ranking_report.json")
OUTPUT_DIR = os.path.join(VERIFICATION_FOLDER)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load JSON
with open(REPORT_FILE) as f:
    data = json.load(f)

# Collect all method names
all_methods = set()
for entry in data:
    all_methods.add(entry["method"])
    id_ranks = entry.get("id_ranks", {})
    all_methods.update(id_ranks.keys())

# Assign a fixed color to each method
color_map = plt.get_cmap("tab10")
method_colors = {
    method: color_map(i % 10) for i, method in enumerate(sorted(all_methods))
}

# Collect ranks per method pair
rank_counts = defaultdict(lambda: defaultdict(list))
for entry in data:
    method_self = entry["method"]
    id_ranks = entry.get("id_ranks", {})

    for method_neighbor, neighbors in id_ranks.items():
        ranks = [n["rank"] for n in neighbors]
        rank_counts[method_self][method_neighbor].extend(ranks)

# Plot each method vs neighbors
for method_self, neighbors_dict in rank_counts.items():
    plt.figure(figsize=(8, 6))
    for method_neighbor, ranks in neighbors_dict.items():
        if not ranks:
            continue
        max_rank = max(ranks)
        counts = [ranks.count(r) for r in range(1, 21)]
        plt.scatter(
            range(0, 20),
            counts,
            label=method_neighbor,
            color=method_colors[method_neighbor],
        )

    plt.title(f"mc3d-id self reported rank for {method_self}")
    plt.xlabel("Rank")
    plt.ylabel("Occurrence")
    plt.legend(title="method")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{method_self}_rank_distribution.png"))
    plt.close()

print(f"Plots saved to {OUTPUT_DIR}")
