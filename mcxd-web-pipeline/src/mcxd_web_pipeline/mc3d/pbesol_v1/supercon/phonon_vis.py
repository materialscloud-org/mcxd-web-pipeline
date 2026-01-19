#!/usr/bin/env python

import time

import aiida
from aiida import orm
from aiida.common.exceptions import ProfileConfigurationError
from phonon_web_tools import convert_qe_phonon_data
from tqdm import tqdm


def convert_supercon_aiida_to_phonon_dict(
    matdyn_retrieved_node, pw_calcjob_node, phonon_band_labels
):
    with (
        pw_calcjob_node.base.repository.open("aiida.in") as f1,
        pw_calcjob_node.get_retrieved_node().open("aiida.out") as f2,
        matdyn_retrieved_node.open("phonon_displacements.dat") as f3,
    ):
        phonon_data = convert_qe_phonon_data(
            f1,
            f2,
            f3,
            highsym_qpts=phonon_band_labels,
        )
    return phonon_data


def populate_supercon_phonon_vis(
    base_coll, target_coll, aiida_profile: str, regen_existing=False
):
    """Populate the supercon phonon visualization MongoDB collection."""
    try:
        aiida.load_profile(aiida_profile, allow_switch=True)
    except ProfileConfigurationError:
        print(f"{aiida_profile} profile not found, skipping.")
        return

    entries = list(base_coll.find())

    start_time = time.time()

    for entry in tqdm(entries, desc="Populating MongoDB"):
        mc3d_id = entry["_id"]
        if not regen_existing and target_coll.find_one({"_id": mc3d_id}) is not None:
            # document exists, skip
            continue

        phonons_set = entry.get("phonons", {})

        mr_uuid = phonons_set.get("matdyn_retrieved_uuid")
        pw_uuid = phonons_set.get("pw_uuid")
        pb_uuid = phonons_set.get("phonon_bands_uuid")

        if all([mr_uuid, pw_uuid, pb_uuid]):
            mr_node = orm.load_node(mr_uuid)
            pw_node = orm.load_node(pw_uuid)
            pb_node = orm.load_node(pb_uuid)

            pw_calcjob = pw_node.called[0]

            phonon_data = convert_supercon_aiida_to_phonon_dict(
                mr_node, pw_calcjob, pb_node.labels
            )

            phonon_data["_id"] = mc3d_id
            target_coll.replace_one({"_id": mc3d_id}, phonon_data, upsert=True)

    end_time = time.time()
    print(f"Total time taken: {end_time - start_time:.2f} seconds")
