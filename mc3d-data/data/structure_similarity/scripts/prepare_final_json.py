import os
import json
from glob import glob
from tqdm import tqdm

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

R_CUT = float(os.getenv("R_CUT", 3.0))
N_MAX = int(os.getenv("N_MAX", 2))
L_MAX = int(os.getenv("L_MAX", 1))

KEEP_VALUE = 25  # number of similar structures to keep.

PARAM_TAG = f"{R_CUT}_{N_MAX}_{L_MAX}"

FILESIM_DIR = os.path.join(SCRIPT_DIR, f"../similarity_files/{PARAM_TAG}")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, f"../similarity_metric_{PARAM_TAG}.json")

print("\nMerging per-structure similarity JSONs")
print("-" * 60)
print(f"{'R_CUT:':<20}{R_CUT}")
print(f"{'N_MAX:':<20}{N_MAX}")
print(f"{'L_MAX:':<20}{L_MAX}")
print(f"{'Input dir:':<20}{FILESIM_DIR}")
print(f"{'Output file:':<20}{OUTPUT_FILE}")
print("-" * 60)

merged_data = []

json_files = glob(os.path.join(FILESIM_DIR, "*.json"))
print(f"Found {len(json_files)} JSON files to merge")

# main loop to prepare the final json from the similarity directory.
for fpath in tqdm(json_files, desc="Merging JSONs"):
    with open(fpath) as f:
        neighbors = json.load(f)

    # Extract structure id and method from file itself
    fname = os.path.basename(fpath)[:-5]  # remove .json
    if "_" in fname:
        structure_id, method = fname.split("_", 1)
    else:
        structure_id, method = fname, "unknown"

    # Convert neighbors
    fixed_neighbors = []
    for n in neighbors[0:KEEP_VALUE]:
        neighbor_fname = n["filename"]
        if neighbor_fname.endswith(".cif"):
            neighbor_fname = neighbor_fname[:-4]
        if "_" in neighbor_fname:
            neighbor_id, neighbor_method = neighbor_fname.split("_", 1)
        else:
            neighbor_id, neighbor_method = neighbor_fname, "unknown"

        fixed_neighbors.append(
            {
                "id": neighbor_id,
                "m": neighbor_method.split(".")[0],
                "s": n["similarity"],
            }
        )

    merged_data.append(
        {"id": structure_id, "m": method.split(".")[0], "n": fixed_neighbors}
    )

print("Writing to disk - this may take a while.")

# Save final JSON
with open(OUTPUT_FILE, "w") as f:
    json.dump(merged_data, f, indent=2)

# ----------------- SUMMARY -----------------
total_structures = len(merged_data)
total_neighbors = sum(len(d["n"]) for d in merged_data)

print("-" * 60)
print("Merge complete")
print(f"{'Total structures:':<30}{total_structures}")
print(f"{'Total neighbor entries:':<30}{total_neighbors}")
print(f"Merged JSON saved to: {OUTPUT_FILE}")
print("-" * 60)
