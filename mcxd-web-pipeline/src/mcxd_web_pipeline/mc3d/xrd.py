"""
Tools to calculate powdered XRD with pymatgen.

Adapted from https://github.com/materialscloud-org/xrd-simulation by Nataliya Paulish.
"""

import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import aiida
import numpy as np
import pymatgen.analysis.diffraction.xrd as xrd
import tqdm
from aiida import orm
from aiida.common.exceptions import ProfileConfigurationError
from pymongo import MongoClient

# Run on multiple cores, but keep some free:
NUM_CORES = max(1, os.cpu_count() - 2)

# Process-local MongoDB singleton (each worker process gets its own instance)
_MONGO_CLIENT = None
_MONGO_DB = None


def get_mongo_db(mongo_uri, mongo_db_name):
    """
    Lazily create and cache a MongoClient per process and return the DB handle.
    """
    global _MONGO_CLIENT, _MONGO_DB
    if _MONGO_DB is None:
        _MONGO_CLIENT = MongoClient(
            mongo_uri,
            maxPoolSize=10,
            connectTimeoutMS=20000,
            socketTimeoutMS=60000,
        )
        _MONGO_DB = _MONGO_CLIENT[mongo_db_name]
    return _MONGO_DB


def calc_pattern(pmg_struct, wavelength="CuKa", two_th_range=(0, 90)):
    """
    Calculate powder xray diffraction pattern for a given structure using pymatgen XRDCalculator.
    """
    xrd_calc = xrd.XRDCalculator(wavelength)
    pattern = xrd_calc.get_pattern(pmg_struct, two_theta_range=two_th_range)
    return pattern


def run_xrd_simulation(
    pmg_struct,
    wavelength_list=("CuKa", "MoKa", "CrKa", "FeKa", "CoKa", "AgKa"),
    two_theta_range=(0, 90),
    precision=4,
):
    """
    Calculate XRDPatterns for a given pymatgen structure and wavelength list.

    Returns a dictionary with wavelength, angular range, peak positions, intensities,
    and hkl indices. Peak positions and intensities are rounded according to `precision`.
    """

    res = {}

    for wavelength in wavelength_list:
        pattern = calc_pattern(pmg_struct, wavelength, two_theta_range)
        angles = np.around(pattern.x, decimals=precision).tolist()
        intensities = np.around(pattern.y, decimals=precision).tolist()
        hkls = []
        for reflection in pattern.hkls:
            hkls.append(reflection[0]["hkl"])

        res[wavelength] = {
            "angular_range": list(two_theta_range),
            "peaks_positions": angles,
            "intensities": intensities,
            "hkls": hkls,
        }
    return res


def run_and_inject_one_xrd(mongo_uri, mongo_db_name, xrd_coll_name, entry):
    """
    Function to run a single XRD and inject into MongoDB.
    Intended to be called inside a worker process.
    """
    mongo_db = get_mongo_db(mongo_uri, mongo_db_name)

    mc_id = entry["_id"]

    if mongo_db[xrd_coll_name].find_one({"_id": mc_id}) is not None:
        return

    structure_uuid = entry["general"]["structure_uuid"]
    sd_node = orm.load_node(structure_uuid)
    pmg_structure = sd_node.get_pymatgen_structure()

    xrd_data = run_xrd_simulation(pmg_structure)

    doc = {"_id": mc_id, "data": xrd_data}

    mongo_db[xrd_coll_name].update_one(
        {"_id": mc_id},
        {"$set": doc},
        upsert=True,
    )


def populate_xrd_parallel(
    mongo_uri,
    mongo_db_name,
    aiida_profile,
    base_coll_name,
    xrd_coll_name,
    recheck=False,
):
    """
    Populate the XRD collection for a single subdb.
    """
    try:
        aiida.load_profile(aiida_profile, allow_switch=True)
    except ProfileConfigurationError:
        print(f"{aiida_profile} profile not found, skipping.")
        return

    mdb = MongoClient(mongo_uri)[mongo_db_name]

    if xrd_coll_name in mdb.list_collection_names() and not recheck:
        print(f"Collection {xrd_coll_name} exists, skipping data injection.")
        return

    print(f"Injecting {xrd_coll_name}")

    base_coll = mdb[base_coll_name]

    # Only fetch what you actually use: _id and general.structure_uuid
    entries = list(
        base_coll.find(
            {},
            {
                "_id": 1,
                "general.structure_uuid": 1,
            },
        )
    )

    if not entries:
        print("No entries found to process.")
        return

    # Initialize the tqdm progress bar
    with tqdm.tqdm(total=len(entries), desc="Processing entries") as pbar:
        with ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
            futures = {
                executor.submit(
                    run_and_inject_one_xrd,
                    mongo_uri,
                    mongo_db_name,
                    xrd_coll_name,
                    entry,
                ): entry
                for entry in entries
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    mc_id = futures[future].get("_id", "UNKNOWN_ID")
                    print(f"An error occurred for _id={mc_id}: {e}")
                finally:
                    pbar.update(1)
