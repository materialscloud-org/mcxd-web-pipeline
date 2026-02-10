import os
import json
from collections import defaultdict

# --- CONFIG ---
R_CUT = os.getenv("R_CUT", "7.0")
N_MAX = os.getenv("N_MAX", "4")
L_MAX = os.getenv("L_MAX", "2")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIMILARITY_DIR = os.path.join(
    SCRIPT_DIR, "../similarity_files", f"{R_CUT}_{N_MAX}_{L_MAX}"
)
TOP_N = 1000  # number of top neighbors to consider per structure
VERIFICATION_FOLDER = os.path.join(SCRIPT_DIR, "../verification")
os.makedirs(VERIFICATION_FOLDER, exist_ok=True)
REPORT_FILE = os.path.join(VERIFICATION_FOLDER, "method_ranking_report.json")

# --- LOAD ALL FILES ---
files = [f for f in os.listdir(SIMILARITY_DIR) if f.endswith(".json")]
report = []

for f in files:
    filepath = os.path.join(SIMILARITY_DIR, f)
    with open(filepath) as jf:
        neighbors = json.load(jf)

    # Parse own structure ID and method
    basename = os.path.splitext(f)[0]  # e.g., mc3d-100_pbe-v1
    if "_" in basename:
        mcid, method = basename.split("_", 1)
    else:
        mcid, method = basename, "unknown"

    method = method.split(".")[0]
    # Collect neighbors of same mcid, grouped by method
    method_groups = defaultdict(list)

    for rank, n in enumerate(neighbors[:TOP_N], start=1):
        n_fname = n["filename"]
        n_sim = n.get("similarity", 0)
        # Parse neighbor mcid and method
        if "_" in n_fname:
            n_mcid, n_method = os.path.splitext(n_fname)[0].split("_", 1)
        else:
            n_mcid, n_method = os.path.splitext(n_fname)[0], "unknown"

        if n_mcid == mcid:
            method_groups[n_method].append({"rank": rank, "similarity": n_sim})

    # Build report entry
    if method_groups:
        report.append(
            {
                "mc3d_id": mcid,
                "method": method,
                "id_ranks": method_groups,
            }
        )

# --- SAVE REPORT ---
with open(REPORT_FILE, "w") as f:
    json.dump(report, f, indent=2)

print(f"Method ranking report saved to {REPORT_FILE}")
