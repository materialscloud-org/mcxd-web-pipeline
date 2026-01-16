import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..utils import (
    get_cached_data,
    return_one_mongodb_entry,
    validate_and_return_collection,
)

router = APIRouter(prefix="/mc2d", tags=["mc2d"])

MC2D_METHODS = ["pbe-v1"]


def validate_method(method: str):
    if method not in MC2D_METHODS:
        raise HTTPException(status_code=404, detail=f"Methodology {method} not found")


@router.get("/info")
async def mc2d_info():
    """Return general information about the mc2d database"""
    method_counts = {}
    for method in MC2D_METHODS:
        coll = validate_and_return_collection("mc2d", f"{method}/base")
        method_counts[method] = coll.estimated_document_count()
    return {"method-counts": method_counts}


@router.get("/{method}/overview")
async def mc2d_overview(method: str):
    """Return the overview list of all structures and their properties"""
    validate_method(method)
    data = get_cached_data("mc2d", f"{method}/overview")
    return JSONResponse(content=json.loads(data))


@router.get("/{method}/meta")
async def mc2d_metadata(method: str):
    """Return the metadata for the specific subdatabase"""
    validate_method(method)
    return return_one_mongodb_entry("mc2d", f"{method}/meta", "metadata")


@router.get("/{method}/structure-uuids")
async def mc2d_structure_uuids(method: str):
    """Return structure uuids for a specific method"""
    validate_method(method)
    coll = validate_and_return_collection("mc2d", f"{method}/structure-uuids")
    results = {}
    for doc in coll.find():
        results[str(doc["_id"])] = doc["uuid"]
    return results


@router.get("/{method}/{contribution}")
async def mc2d_contribution_ids(method: str, contribution: str):
    """Return available ids for a specific contribution"""
    validate_method(method)
    coll = validate_and_return_collection("mc2d", f"{method}/{contribution}")
    ids = coll.find({}, {"_id": 1}).hint("_id_")
    return {"available_ids": [doc["_id"] for doc in ids]}


@router.get("/{method}/{contribution}/{entry_id}")
async def mc2d_contribution_entry(method: str, contribution: str, entry_id: str):
    """Return a single entry from a contribution"""
    validate_method(method)
    return return_one_mongodb_entry("mc2d", f"{method}/{contribution}", entry_id)
