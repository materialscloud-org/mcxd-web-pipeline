# routers/mc_common.py
import json
from typing import Sequence

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..utils import (
    get_cached_data,
    return_all_mongodb_entries,
    return_one_mongodb_entry,
    validate_and_return_collection,
)


def build_mc_router(
    *,
    db_name: str,
    prefix: str,
    tag: str,
    methods: Sequence[str],
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    def validate_method(method: str):
        if method not in methods:
            raise HTTPException(
                status_code=404, detail=f"Methodology {method} not found"
            )

    @router.get("/dataset-index/{entry_id}")
    async def dataset_index(entry_id: str):
        """Return all available datasets/contributions for a MC-ID"""
        return return_one_mongodb_entry(db_name, "dataset-index", entry_id)

    @router.get("/info")
    async def mc_info():
        """Return general information about the mc database"""
        method_counts = {}
        for method in methods:
            coll = validate_and_return_collection(db_name, f"{method}_core_base")
            method_counts[method] = coll.estimated_document_count()
        return {"method-counts": method_counts}

    @router.get("/{method}/overview")
    async def mc_overview(method: str):
        """Return the overview list of all structures and their properties"""
        validate_method(method)
        data = get_cached_data(db_name, f"{method}_overview")
        return JSONResponse(content=json.loads(data))

    @router.get("/{method}/meta")
    async def mc_metadata(method: str):
        """Return the metadata for the specific subdatabase"""
        validate_method(method)
        data = return_all_mongodb_entries(db_name, f"{method}_meta")

        core = next(d for d in data if d.get("id") == "core")
        rest = [d for d in data if d.get("id") != "core"]

        result = {"index-columns": [], "info": {}}
        result["index-columns"].extend(core.get("index-columns", []))
        result["info"].update(core.get("info", {}))

        for d in rest:
            result["index-columns"].extend(d.get("index-columns", []))
            if "info" in d:
                result["info"].update(d["info"])
        return result

    @router.get("/{method}/structure-uuids")
    async def mc_structure_uuids(method: str):
        """Return structure uuids for a specific method"""
        validate_method(method)
        coll = validate_and_return_collection(db_name, f"{method}_core_structure-uuids")
        return {str(doc["_id"]): doc["uuid"] for doc in coll.find()}

    @router.get("/{method}/{contribution}")
    async def mc_contribution_ids(method: str, contribution: str):
        """Return available ids for a specific contribution"""
        validate_method(method)
        coll = validate_and_return_collection(db_name, f"{method}_{contribution}")
        ids = coll.find({}, {"_id": 1}).hint("_id_")
        return {"available_ids": [doc["_id"] for doc in ids]}

    @router.get("/{method}/{contribution}/{entry_id}")
    async def mc_contribution_entry(method: str, contribution: str, entry_id: str):
        """Return a single entry from a contribution"""
        validate_method(method)
        return return_one_mongodb_entry(db_name, f"{method}_{contribution}", entry_id)

    return router
