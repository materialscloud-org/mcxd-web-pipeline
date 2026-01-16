import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..utils import (
    get_cached_data,
    return_all_mongodb_entries,
    return_one_mongodb_entry,
    validate_and_return_collection,
)

router = APIRouter(prefix="/mc3d", tags=["mc3d"])

MC3D_METHODS = ["pbe-v1", "pbesol-v1", "pbesol-v2"]


def validate_method(method: str):
    if method not in MC3D_METHODS:
        raise HTTPException(status_code=404, detail=f"Methodology {method} not found")


@router.get("/dataset-index/{entry_id}")
async def dataset_index(entry_id: str):
    """Return all available datasets/contributions for a MC-ID"""
    return return_one_mongodb_entry("mc3d", "dataset-index", entry_id)


@router.get("/info")
async def mc3d_info():
    """Return general information about the mc3d database"""
    method_counts = {}
    for method in MC3D_METHODS:
        coll = validate_and_return_collection("mc3d", f"{method}_core_base")
        method_counts[method] = coll.estimated_document_count()
    return {"method-counts": method_counts}


@router.get("/{method}/overview")
async def mc3d_overview(method: str):
    """Return the overview list of all structures and their properties"""
    validate_method(method)
    data = get_cached_data("mc3d", f"{method}_overview")
    return JSONResponse(content=json.loads(data))


@router.get("/{method}/meta")
async def mc3d_metadata(method: str):
    """Return the metadata for the specific subdatabase"""
    validate_method(method)
    data = return_all_mongodb_entries("mc3d", f"{method}_meta")

    core = next(d for d in data if d.get("id") == "core")
    rest = [d for d in data if d.get("id") != "core"]

    result = {"index-columns": [], "info": {}}
    # 1. Merge core first
    result["index-columns"].extend(core.get("index-columns", []))
    result["info"].update(core.get("info", {}))

    # 2. Merge remaining dictionaries next (in order)
    for d in rest:
        result["index-columns"].extend(d.get("index-columns", []))
        if "info" in d:
            result["info"].update(d["info"])
    return result


@router.get("/{method}/structure-uuids")
async def mc3d_structure_uuids(method: str):
    """Return structure uuids for a specific method"""
    validate_method(method)
    coll = validate_and_return_collection("mc3d", f"{method}_core_structure-uuids")
    results = {}
    for doc in coll.find():
        results[str(doc["_id"])] = doc["uuid"]
    return results


@router.get("/{method}/{contribution}")
async def mc3d_contribution_ids(method: str, contribution: str):
    """Return available ids for a specific contribution"""
    validate_method(method)
    coll = validate_and_return_collection("mc3d", f"{method}_{contribution}")
    ids = coll.find({}, {"_id": 1}).hint("_id_")
    return {"available_ids": [doc["_id"] for doc in ids]}


@router.get("/{method}/{contribution}/{entry_id}")
async def mc3d_contribution_entry(method: str, contribution: str, entry_id: str):
    """Return a single entry from a contribution"""
    validate_method(method)
    return return_one_mongodb_entry("mc3d", f"{method}_{contribution}", entry_id)
