import os
import requests
from tqdm import tqdm
import time

# set the cwd to the directory of this script.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STRUCTURES_DIR = os.path.join(SCRIPT_DIR, "..", "structures")
os.makedirs(STRUCTURES_DIR, exist_ok=True)

METHOD_NAMES = ["pbesol-v2", "pbesol-v1", "pbe-v1"]


BASE_MCXD_URL = "https://mcxd-api.materialscloud.org/mc3d/"
TAIL_MCXD_URL = "structure-uuids"

BASE_AIIDA_URL = "https://aiida.dev.materialscloud.org/mc3d-pbesol-v2/api/v4/nodes/"
TAIL_AIIDA_URL = "/download?download_format=cif"


# map each method to a url. keys gets saved as the filename and will be used in parsing later.
method_base_urls = {
    "pbesol-v2": "https://aiida.dev.materialscloud.org/mc3d-pbesol-v2/api/v4/nodes/",  # use dev urls to not nuke the backend.
    "pbesol-v1": "https://aiida.dev.materialscloud.org/mc3d-pbesol-v1/api/v4/nodes/",
    "pbe-v1": "https://aiida.dev.materialscloud.org/mc3d-pbe-v1/api/v4/nodes/",
}

# Download the structures from backend endpoint.

full_data = []
for method in METHOD_NAMES:
    url = f"{BASE_MCXD_URL}{method}/{TAIL_MCXD_URL}"
    response = requests.get(url)
    response.raise_for_status()
    structures = response.json()

    for id_mc, uuid in structures.items():
        full_data.append(
            {
                "id": id_mc,
                "method": method,
                "uuid": uuid,
                "base_url": method_base_urls[method],
            }
        )

print("\n UUID Download Summary")
print("-" * 40)
print(f"Methods processed: {', '.join(METHOD_NAMES)}")
print(f"Total structures found: {len(full_data)}\n")
print("-" * 40)


skip_files = 0
dl_files = 0
failed_files = 0
for entry in tqdm(full_data, desc="Downloading CIFs"):
    file_name = f"{entry['id']}_{entry['method']}.cif"
    file_path = os.path.join(STRUCTURES_DIR, file_name)

    if os.path.exists(file_path):
        skip_files += 1
        continue

    url = f"{entry['base_url']}{entry['uuid']}{TAIL_AIIDA_URL}"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()

        # Filter out comment lines to improve later io
        clean_lines = [
            line.rstrip() + "\n"
            for line in r.text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

        with open(file_path, "w") as f:
            f.writelines(clean_lines)
        dl_files += 1
    except Exception as e:
        print(f"Failed to download {file_name}: {e}")
        failed_files += 1

    time.sleep(0.05)


print(f"{'Downloaded:':<20}{dl_files:>5}")
print(f"{'Skipped (already exist):':<20}{skip_files:>5}")
print(f"{'Failed:':<20}{failed_files:>5}")
print("-" * 40)
print("Script complete!\n")
