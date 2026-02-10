"""
Module to inject MCXD data into a MongoDB database.

* Step 1: Populate the database from the pre-generated JSON files.
* Step 2: Generate derived collections from the base data.
    * structure uuids
    * overview table
* Step 3: custom data injections
    * xrd
    * interactive phonon vis
"""

import json
from collections import defaultdict
from pathlib import Path

from pymongo import MongoClient

from mcxd_web_pipeline.config import CONFIG, REPO_ROOT
from mcxd_web_pipeline.mc3d.pbesol_v1.supercon.phonon_vis import (
    populate_supercon_phonon_vis,
)
from mcxd_web_pipeline.mc3d.xrd import populate_xrd_parallel


def get_data_folder(mcxd_type: str) -> Path:
    """Get the data folder for a given MCXD type."""
    return REPO_ROOT / f"{mcxd_type}-data" / "data"


def _check_mongodb(client):
    try:
        client.admin.command("ping")
        print("MongoDB connection successful.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        exit(1)


def _get_aiida_profiles(mcxd_type) -> dict[str, str]:
    return {k: v["aiida_profile"] for k, v in CONFIG["info"][mcxd_type].items()}


def _check_aiida_profiles(aiida_profiles):
    from aiida.manage.configuration import load_config

    aiida_cfg = load_config()
    aiida_profile_names = list(aiida_cfg.profile_names)
    for sub_label, profile in aiida_profiles.items():
        if profile not in aiida_profile_names:
            print(
                "Warning: AiiDA profile",
                profile,
                "for dataset",
                f"{sub_label}",
                "not found.",
            )


class McMongoInjector:
    def __init__(self, mcxd_type: str = "mc3d"):
        self.mcxd_type = mcxd_type

        self.mongo_uri = CONFIG["mongo"]["uri"]
        self.mongo_db_name = CONFIG["mongo"][f"{mcxd_type}_db_name"]

        self.client = MongoClient(self.mongo_uri)
        _check_mongodb(self.client)

        self.db = self.client[self.mongo_db_name]

        self.aiida_profiles = _get_aiida_profiles(self.mcxd_type)
        _check_aiida_profiles(self.aiida_profiles)

        self.dataset_labels = {}

    #### Methods to deal with the pre-generated JSON data files ####

    def _inject_base_json(self, coll_name: str, path: Path, drop: bool = False):
        if drop and coll_name in self.db.list_collection_names():
            print(f"Collection {coll_name} exists, dropping it!")
            self.db[coll_name].drop()

        with path.open("r") as fhandle:
            data = json.load(fhandle)

        for mc_id, val in data.items():
            entry = {"_id": mc_id, **val}
            self.db[coll_name].replace_one({"_id": mc_id}, entry, upsert=True)

    def _inject_meta_json(self, coll_name: str, label: str, path: Path):
        with path.open("r") as fhandle:
            data = json.load(fhandle)

        self.db[coll_name].replace_one({"_id": label}, data, upsert=True)

    def inject_file_data(self, method: str = "all"):
        """Populate the database from base.json and meta.json files.

        Relatively fast, can be done on each update.
        """
        for method_path in get_data_folder(self.mcxd_type).iterdir():
            method_ = method_path.name
            if method != "all" and method_ != method:
                continue

            print(f"Handling {method_}/core/base")
            base_path = method_path / "core" / "base.json"
            meta_path = method_path / "core" / "meta.json"
            self._inject_base_json(f"{method_}_core_base", base_path)
            self._inject_meta_json(f"{method_}_meta", "core", meta_path)

            self.dataset_labels[method_] = ["core"]

            # Extra contributions
            for contrib_path in method_path.iterdir():
                contrib = contrib_path.name
                if contrib == "core":
                    continue
                contrib_base_path = contrib_path / "base.json"
                contrib_meta_path = contrib_path / "meta.json"
                if not contrib_base_path.is_file() or not contrib_meta_path.is_file():
                    print(f"Warning, missing files for {method_}/{contrib}, skipping.")
                    continue
                print(f"Handling {method_}/{contrib}/base")
                self._inject_base_json(f"{method_}_{contrib}_base", contrib_base_path)
                self._inject_meta_json(f"{method_}_meta", contrib, contrib_meta_path)
                self.dataset_labels[method_].append(contrib)

    #### Derived data from the base json files ####

    def _populate_structure_uuids(self, method):
        """Extract structure_uuids from the core collection"""

        coll_name = f"{method}_core_structure-uuids"
        coll_core = f"{method}_core_base"

        if coll_name in self.db.list_collection_names():
            print(f"Collection {coll_name} exists, dropping it!")
            self.db[coll_name].drop()

        print(f"Populating {coll_name}")
        for doc in self.db[coll_core].find():
            if self.mcxd_type == "mc2d":
                uuid = doc.get("general", {}).get("structure_relaxed_uuid", None)
            else:
                uuid = doc.get("general", {}).get("structure_uuid", None)
                if uuid is None:
                    uuid = doc.get("general", {}).get("uuid_structure", None)
            if uuid:
                entry = {"_id": doc["_id"], "uuid": uuid}
                self.db[coll_name].replace_one({"_id": doc["_id"]}, entry, upsert=True)

    def _project_overview_columns(self, method, label):
        meta_coll_name = f"{method}_meta"
        metadata = self.db[meta_coll_name].find_one({"_id": label})

        if metadata is None:
            print(f"Metadata for {method}/{label} not found, skipping.")
            return {}

        cname = f"{method}_{label}_base"

        pipeline_project = {}
        for col in metadata["index-columns"]:
            if "array_index" in col:
                pipeline_project[col["data_label"]] = {
                    "$arrayElemAt": [f"${col['data_path']}", col["array_index"]]
                }
            else:
                pipeline_project[col["data_label"]] = f"${col['data_path']}"
        if not pipeline_project:
            return {}
        pipeline = [{"$project": pipeline_project}]
        result = list(self.db[cname].aggregate(pipeline))
        return {d["_id"]: d for d in result}

    def _populate_overview_table(self, method):
        target_coll = f"{method}_overview"

        if target_coll in self.db.list_collection_names():
            print(f"Collection {target_coll} exists, dropping it!")
            self.db[target_coll].drop()

        print(f"Populating {target_coll}")

        # for each sub-dataset, project the table column data
        overview_columns = self._project_overview_columns(method, "core")

        # "contributed" datasets
        for label in self.dataset_labels[method]:
            if label == "core":
                continue
            extra_columns = self._project_overview_columns(method, label)
            for doc_id, doc in extra_columns.items():
                if doc_id in overview_columns:
                    overview_columns[doc_id].update(doc)
                else:
                    # contributed datasets should not have new entries
                    # overview_columns[doc_id] = doc
                    print(
                        f"Warning: dataset {method}/{label} has entry {doc_id} not in core. Skipping."
                    )

        # Insert merged docs into overview collection
        if overview_columns:
            to_insert = list(overview_columns.values())
            self.db[target_coll].insert_many(to_insert)
            print(f"Inserted {len(to_insert)} merged documents into {target_coll}")
        else:
            print(f"No documents to insert into {target_coll}")

    def populate_base_derived(self, method: str = "all"):
        """Populate the base derived collections for each method."""
        if method == "all":
            methods = list(self.dataset_labels.keys())
        else:
            methods = [method]

        for method in methods:
            self._populate_structure_uuids(method)
            self._populate_overview_table(method)

    #### Custom data injections ####

    def populate_xrd(self, method: str = "all", recheck: bool = False):
        """Populate the XRD collections."""
        if method == "all":
            methods = list(self.aiida_profiles.keys())
        else:
            methods = [method]

        for m in methods:
            populate_xrd_parallel(
                self.mongo_uri,
                self.mongo_db_name,
                self.aiida_profiles[m],
                f"{m}_core_base",
                f"{m}_core_xrd",
                recheck=recheck,
            )

    def populate_structure_similarity(
        self,
        max_neighbors=None,
        min_similarity=None,
    ):
        rootpath = get_data_folder(mcxd_type="mc3d")
        json_sim_path = rootpath / "structure_similarity/similarity.json"

        with open(json_sim_path) as f:
            merged_data = json.load(f)

        sim_collection = self.db["structure-similarity"]

        # Group entries by structure ID
        grouped = defaultdict(dict)

        for entry in merged_data:
            struct_id = entry["id"]
            method = entry["m"]
            neighbors = entry["n"]

            # Filter by max_n / min_s
            filtered_neighbors = neighbors
            if min_similarity is not None:
                filtered_neighbors = [
                    n for n in filtered_neighbors if n.get("s", 0) >= min_similarity
                ]
            if max_neighbors is not None:
                filtered_neighbors = filtered_neighbors[:max_neighbors]

            grouped[struct_id][method] = filtered_neighbors

        # Build documents for MongoDB
        docs = []
        for struct_id, methods_dict in grouped.items():
            doc = {"_id": struct_id}
            doc.update(methods_dict)
            docs.append(doc)

        # Insert/update in MongoDB
        for doc in docs:
            sim_collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    def populate_supercon_phonon_vis(self, regen_existing=False):
        """Populate the XRD collections."""

        supercon_base_coll = self.db["pbesol-v1_supercon_base"]
        phonon_vis_coll = self.db["pbesol-v1_supercon_phonon-vis"]
        aiida_profile = self.aiida_profiles["pbesol-v1-supercon"]

        populate_supercon_phonon_vis(
            supercon_base_coll,
            phonon_vis_coll,
            aiida_profile,
            regen_existing=regen_existing,
        )

    def populate_dataset_index(self):
        """Populate the contributions index for each MCXD-ID."""

        target_coll = "dataset-index"

        SKIP_COLLECTIONS = ["overview", "structure-uuids"]

        coll_names = self.db.list_collection_names()

        # contrib_index[mcxd_id][method] -> list of collection-suffixes
        contrib_index = defaultdict(lambda: defaultdict(list))

        for coll_name in coll_names:
            # skip the target collection itself if it already exists
            if coll_name == target_coll:
                continue

            if any(n in coll_name for n in SKIP_COLLECTIONS):
                continue

            coll = self.db[coll_name]

            # split collection name: "pbesol-v1_core_base" -> method="pbesol-v1", rest="core_base"
            parts = coll_name.split("_")
            method = parts[0]
            rest = "_".join(parts[1:]) if len(parts) > 1 else ""

            # check if the collection has entries enumerated by the mcxd-id
            sample = coll.find_one()
            if not sample or "_id" not in sample:
                continue

            # only consider collections whose _id looks like an mcxd-id
            if f"{self.mcxd_type}-" not in str(sample["_id"]):
                continue

            # get all mcxd-ids
            ids = coll.distinct("_id")

            for _id in ids:
                contrib_index[_id][method].append(rest)

        if target_coll in self.db.list_collection_names():
            print(f"Collection {target_coll} exists, dropping it!")
            self.db[target_coll].drop()

        print(f"Populating {target_coll}")
        out_coll = self.db[target_coll]

        # write one document per mcxd-id
        docs = []
        for mcxd_id, methods_dict in contrib_index.items():
            docs.append(
                {
                    "_id": mcxd_id,
                    "index": dict(methods_dict),
                }
            )

        if docs:
            out_coll.insert_many(docs)
        else:
            print("No MCXD-indexed contributions found.")
