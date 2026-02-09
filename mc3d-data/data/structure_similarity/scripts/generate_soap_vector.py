import numpy as np
from glob import glob
from ase.io import read
from dscribe.descriptors import SOAP
from tqdm import tqdm
from sklearn.preprocessing import normalize
import json
import os
import sys

from multiprocessing import Pool, cpu_count

# set the cwd to the directory of this script.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STRUCTURES_DIR = os.path.join(SCRIPT_DIR, "..", "structures")
SOAP_DIR = os.path.join(SCRIPT_DIR, "..", "soap")

os.makedirs(SOAP_DIR, exist_ok=True)

R_CUT = float(os.getenv("R_CUT", 3))
N_MAX = int(os.getenv("N_MAX", 2))
L_MAX = int(os.getenv("L_MAX", 1))

SOAP_VECTORS_FILE = os.path.join(SOAP_DIR, f"soap_vectors_{R_CUT}_{N_MAX}_{L_MAX}.npy")

print(SOAP_VECTORS_FILE)

VALID_FILES_FILE = os.path.join(SOAP_DIR, f"valid_files_{R_CUT}_{N_MAX}_{L_MAX}.json")

# ---- Skip if outputs already exist ----
if os.path.exists(SOAP_VECTORS_FILE) and os.path.exists(VALID_FILES_FILE):
    print(
        f"SOAP outputs already exist for parameters "
        f"(R_CUT={R_CUT}, N_MAX={N_MAX}, L_MAX={L_MAX}). Skipping."
    )
    sys.exit(0)


def init_worker(species_list):
    global soap_worker

    soap_worker = SOAP(
        species=species_list,
        r_cut=R_CUT,
        n_max=N_MAX,
        l_max=L_MAX,
        periodic=True,
    )


def compute_soap_worker(fname):
    global soap_worker
    try:
        atoms = read(fname)
        vec = soap_worker.create(atoms).mean(0).astype(np.float32)
        return fname, vec, None

    except Exception as e:
        return fname, None, str(e)


species_list = [z for z in range(1, 87) if z != 85]
structures_files = sorted(glob(f"{STRUCTURES_DIR}/*.cif"))

nproc = max(cpu_count() - 2, 1)

soap_worker = None
structure_vectors = []
valid_files = []

print(
    f"-- RUNNING SOAP VECTOR GENERATION -- R_CUT={R_CUT}, N_MAX={N_MAX}, L_MAX={L_MAX}"
)

with Pool(nproc, initializer=init_worker, initargs=(species_list,)) as pool:
    for fname, vec, err in tqdm(
        pool.imap_unordered(compute_soap_worker, structures_files),
        total=len(structures_files),
        desc="SOAP generation",
    ):
        if err:
            tqdm.write(f"FAILED SOAP {fname}: {err}")
            continue

        structure_vectors.append(vec)
        valid_files.append(fname)

# ---- Save SOAP vectors ----
X = np.vstack(structure_vectors).astype(np.float32)
X = normalize(X)

np.save(SOAP_VECTORS_FILE, X)

# ---- Save valid file list ----
with open(VALID_FILES_FILE, "w") as f:
    json.dump(valid_files, f, indent=2)

# ---- Summary ----
total_files = len(structures_files)
success_files = len(valid_files)
failed_files = total_files - success_files

print("\n SOAP Generation Summary")
print("-" * 50)
print(f"{'Total files processed:':<30}{total_files:>5}")
print(f"{'Successfully processed:':<30}{success_files:>5}")
print(f"{'Failed:':<30}{failed_files:>5}")
print("-" * 50)

print(f"SOAP vectors saved to: {SOAP_VECTORS_FILE}")
print(f"Valid file list saved to: {VALID_FILES_FILE}\n")
