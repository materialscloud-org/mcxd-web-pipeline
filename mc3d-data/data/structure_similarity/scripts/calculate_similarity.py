import os
import json
import numpy as np
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm

CHUNK_SIZE = 10000
N_NEIGHBORS = 100
SIMILARITY_THRESHOLD = 0.001

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_FILESIM_DIR = os.path.join(SCRIPT_DIR, "../similarity_files")

R_CUT = float(os.getenv("R_CUT", 3.0))
N_MAX = int(os.getenv("N_MAX", 2))
L_MAX = int(os.getenv("L_MAX", 1))

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
X = np.load(SOAP_VECTORS_PATH, mmap_mode="r")  # dont load full array at once

with open(VALID_FILES_PATH) as f:
    valid_files = json.load(f)

print(f"Loaded {X.shape[0]} vectors")

nn = NearestNeighbors(
    n_neighbors=min(N_NEIGHBORS + 1, X.shape[0]),
    metric="cosine",
    algorithm="brute",
    n_jobs=-1,
)

print("Fitting nearest neighbor model...")
nn.fit(X)

for start in tqdm(range(0, X.shape[0], CHUNK_SIZE), desc="Computing neighbors"):
    end = min(start + CHUNK_SIZE, X.shape[0])
    X_chunk = X[start:end]

    distances, indices = nn.kneighbors(X_chunk)
    similarities = 1.0 - distances

    for i_local, i_global in enumerate(range(start, end)):
        fname = valid_files[i_global]
        neighbors = []

        for j in range(1, similarities.shape[1]):  # skip self
            neighbor_idx = indices[i_local, j]
            sim = float(similarities[i_local, j])

            if sim < SIMILARITY_THRESHOLD:
                continue

            neighbor_file = os.path.basename(valid_files[neighbor_idx])
            neighbors.append({"filename": neighbor_file, "similarity": sim})

        base_name = os.path.splitext(os.path.basename(fname))[0]
        out_file = os.path.join(FILESIM_DIR, f"{base_name}.json")

        with open(out_file, "w") as f:
            json.dump(neighbors, f, indent=2)

print("\nSimilarity computation complete")
print(f"Output directory: {FILESIM_DIR}\n")
