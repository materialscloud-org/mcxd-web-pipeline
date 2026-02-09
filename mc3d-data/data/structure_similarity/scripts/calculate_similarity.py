import os
import json
import numpy as np
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm

N_NEIGHBORS = 100
CHUNK_SIZE = 10000
SIMILARITY_THRESHOLD = 0.001

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_FILESIM_DIR = os.path.join(SCRIPT_DIR, "../similarity_files")

R_CUT = float(os.getenv("R_CUT", 7.0))
N_MAX = int(os.getenv("N_MAX", 4))
L_MAX = int(os.getenv("L_MAX", 2))

PARAM_TAG = f"{R_CUT}_{N_MAX}_{L_MAX}"
FILESIM_DIR = os.path.join(BASE_FILESIM_DIR, PARAM_TAG)
os.makedirs(FILESIM_DIR, exist_ok=True)

SOAP_VECTORS_PATH = os.path.join(SCRIPT_DIR, f"../soap/soap_vectors_{PARAM_TAG}.npy")
VALID_FILES_PATH = os.path.join(SCRIPT_DIR, f"../soap/valid_files_{PARAM_TAG}.json")

print("\n Similarity computation")
print("-" * 50)
print(f"{'R_CUT:':<20}{R_CUT}")
print(f"{'N_MAX:':<20}{N_MAX}")
print(f"{'L_MAX:':<20}{L_MAX}")
print(f"{'Chunk size:':<20}{CHUNK_SIZE}")
print(f"{'Neighbors:':<20}{N_NEIGHBORS}")
print("-" * 50)

# --- LOAD DATA ---
X = np.load(SOAP_VECTORS_PATH, mmap_mode="r")  # memory-mapped to reduce RAM
with open(VALID_FILES_PATH) as f:
    valid_files = json.load(f)

valid_files = valid_files
print(f"Loaded {X.shape[0]} vectors")

# Process in chunks
for start in range(0, X.shape[0], CHUNK_SIZE):
    print(f"Processing chunk {start} -> {min(start + CHUNK_SIZE, X.shape[0])}")
    end = min(start + CHUNK_SIZE, X.shape[0])
    X_chunk = X[start:end]

    # Fit on full dataset
    nn = NearestNeighbors(
        n_neighbors=N_NEIGHBORS + 1, metric="cosine", algorithm="brute", n_jobs=-1
    )
    nn.fit(X)
    distances, indices = nn.kneighbors(X_chunk)

    similarities = 1.0 - distances

    for i_local, i_global in enumerate(range(start, end)):
        fname = valid_files[i_global]
        neighbors = []

        for j in range(1, N_NEIGHBORS + 1):  # skip self
            neighbor_idx = indices[i_local, j]
            sim = float(similarities[i_local, j])

            neighbor_file = os.path.basename(valid_files[neighbor_idx])
            neighbors.append({"filename": neighbor_file, "similarity": sim})

        # Save each structure's neighbors to its own JSON
        basename = os.path.basename(fname)
        out_file = os.path.join(FILESIM_DIR, f"{basename}.json")
        with open(out_file, "w") as f:
            json.dump(neighbors, f, indent=2)

print("\nSimilarity computation complete")
print(f"Output directory: {FILESIM_DIR}\n")
