"""Pydantic models and functions used for the analysis jupyter notebooks.
"""

import aiida
from aiida import orm
from aiida.orm import load_node

import numpy as np

import re
import pymatgen.symmetry.groups

# Pydantic models:
# One major change: stop using top-level parent-related keys and
# just use all_3D_parents with the first one being always the main parent

from pydantic import BaseModel, Field, constr, ValidationError
from typing import List, Literal, Union, Optional
from uuid import UUID

class AiidaFloat(BaseModel):
    value: float
    uuid: UUID
    
class AiidaFloatList(BaseModel):
    value: List[float]
    uuid: UUID

class Parent3D(BaseModel):
    formula: str
    source_db: Literal["COD", "ICSD", "MPDS"]
    source_db_id: constr(min_length=1)
    space_group_number: Optional[int] = Field(ge=1, le=230, default=None)
    initial_structure_uuid: UUID
    binding_energy_df2: Optional[AiidaFloat] = None
    binding_energy_rvv10: Optional[AiidaFloat] = None
    delta_df2: Optional[AiidaFloat] = None
    delta_rvv10: Optional[AiidaFloat] = None
    opt_structure_df2_uuid: Optional[UUID] = None
    opt_structure_revpbe_uuid: Optional[UUID] = None
    opt_structure_rvv10_uuid: Optional[UUID] = None


class StructureEntry(BaseModel):
    # general/structural/parents:
    formula: str
    formula_reduced: str
    as_extracted_2D_structure_uuid: UUID
    all_3D_parents: List[Parent3D]
    space_group_number: Optional[int] = Field(ge=1, le=230, default=None)
    prototype: Optional[str] = None
    abundance: Optional[float] = None
    optimized_2D_structure_uuid: Optional[UUID] = None
    # label for papers where the structure was exfoliated/studied (mounet18 or campi23):
    citations: Optional[List[str]] = None
    # electronic:
    bands_uuid: Optional[UUID] = None
    band_gap: Optional[AiidaFloat] = None
    fermi_energy: Optional[AiidaFloatList] = None
    magnetic_state: Optional[Literal["non-magnetic", "ferromagnetic", "antiferromagnetic"]] = None
    absolute_magnetization: Optional[AiidaFloat] = None
    total_magnetization: Optional[AiidaFloat] = None
    # vibrational:
    phonon_bands_uuid: Optional[UUID] = None


def get_element_set(formula):
    return set(re.findall(r'[A-Z][a-z]?', formula))

def get_space_group_number(symbol):
    if symbol is None:
        return None
    
    num = None
    
    if "(" in symbol:
        # number is in parenthesis, both the symbol and number
        sp = symbol.split("(")
        symbol = sp[0].strip()
        num = int(sp[1].replace(")", "").strip())
        
    pmg_num = pymatgen.symmetry.groups.SpaceGroup(symbol).int_number
    
    if num:
        # make sure the pymatgen number matches with the one is parenthesis,
        # if it was given
        assert pmg_num == num
    
    return pmg_num

def check_and_return_aiida_prop(prop):
    if prop is None or prop["uuid"] is None:
        return None
    load_node(prop["uuid"])
    return {
        "value": prop.get("value", prop.get("values")),
        "uuid": prop["uuid"],
    }

class ParentsException(Exception):
    pass

def check_consistency_and_merge_parents(p1, p2):
    
    keys = list(set(list(p1.keys()) + list(p2.keys())))
    
    merged = {}
    
    for key in keys:
        val1 = p1.get(key)
        val2 = p2.get(key)
        
        if val1 is None and val2 is None:
            continue
        
        if val1 is None:
            merged[key] = val2
            continue
            
        if val2 is None:
            merged[key] = val1
            continue
            
        if isinstance(val1, dict):
            for k, v1 in val1.items():
                if k not in val1:
                    raise ParentsException(f"{k} not in {val1}")
                v2 = val2[k]
                if isinstance(v1, float) and isinstance(v2, float):
                    if np.abs(v1 - v2) > 1e-4:
                        raise ParentsException(f"{v1} != {v2}")
                else:
                    if v1 != v2:
                        raise ParentsException(f"{v1} != {v2}")
        merged[key] = val1
    return merged

def validate_and_return_parents(entry, formula_2d, log, ignore_top_binding_props=False):
    
    # collect the pydantic fields from the top-level parent
    # note, different entries can use different keys...
    source_db = entry.get("initial_3D_source_db")
    top_level_parent = {
        "formula": entry.get("initial_3D_formula", entry.get("initial_3D_bulk_formula")),
        "source_db_id": entry.get("initial_3D_db_id"),
        "source_db": source_db.upper() if source_db is not None else None,
        "initial_structure_uuid": entry.get("initial_3D_bulk_structure", entry.get("initial_3D_bulk_structure_uuid")),
        "space_group_number": get_space_group_number(entry.get("initial_3D_spg")),
        "opt_structure_df2_uuid": entry.get("relaxed_3D_bulk_structure_df2", entry.get("relaxed_3D_bulk_structure_df2_uuid")),
        "opt_structure_rvv10_uuid": entry.get("relaxed_3D_bulk_structure_rvv10", entry.get("relaxed_3D_bulk_structure_rvv10_uuid")),
        "opt_structure_revpbe_uuid": entry.get("relaxed_3D_bulk_structure_revpbe"),
    }
    if top_level_parent["source_db"] is not None:
        top_level_parent["source_db"] = top_level_parent["source_db"].upper()
    
    if not ignore_top_binding_props:
        top_level_parent["binding_energy_df2"] = check_and_return_aiida_prop(entry.get("binding_energy_per_substructure_per_unit_area_df2"))
        top_level_parent["binding_energy_rvv10"] = check_and_return_aiida_prop(entry.get("binding_energy_per_substructure_per_unit_area_rvv10"))
        top_level_parent["delta_df2"] = check_and_return_aiida_prop(entry.get("delta_df2"))
        top_level_parent["delta_rvv10"] = check_and_return_aiida_prop(entry.get("delta_rvv10"))
        
    raw_parents = entry.get("all_3D_parents", [])
    parents = []
    
    # format the parent list to use pydantic keys
    for parent in raw_parents:
        source_db = parent.get("source_db")
        parents.append({
            "formula": parent.get("formula"),
            "source_db_id": parent.get("db_id"),
            "source_db": source_db.upper() if source_db is not None else None,
            "initial_structure_uuid": parent.get("uuid"),
            "space_group_number": get_space_group_number(parent.get("spg")),
            "binding_energy_df2": check_and_return_aiida_prop(parent.get("binding_energy_per_substructure_per_unit_area_df2")),
            "binding_energy_rvv10": check_and_return_aiida_prop(parent.get("binding_energy_per_substructure_per_unit_area_rvv10")),
            "delta_df2": check_and_return_aiida_prop(parent.get("delta_df2")),
            "delta_rvv10": check_and_return_aiida_prop(parent.get("delta_rvv10")),
        })
    
    # sort parents by 1)df2; 2) rvv10 binding energy. 
    sort_key_func = lambda x: (
        float('inf') if x.get("binding_energy_df2") is None else x["binding_energy_df2"].get("value", float('inf')),
        float('inf') if x.get("binding_energy_rvv10") is None else x["binding_energy_rvv10"].get("value", float('inf'))
    )
    sorted_parents = sorted(parents, key=sort_key_func)
    
    if parents != sorted_parents:
        log("    Warning: parents sorting changed")
    parents = sorted_parents

    if len(parents) > 0:
        merged_parent = check_consistency_and_merge_parents(top_level_parent, parents[0])
        parents[0] = merged_parent
    else:
        parents.append(top_level_parent)
    
    
    # check formulas from aiida
    for parent in parents:
        uuid = parent.get("initial_structure_uuid")
        if uuid:
            structure_node = load_node(uuid)
            aiida_formula = structure_node.get_formula(mode="hill")
            parent_formula = parent.get("formula")
            if parent_formula:
                # just check elements as the formula might be reduced
                if get_element_set(aiida_formula) != get_element_set(parent_formula):
                    raise ParentsException(f"Parent and aiida formula conflict: {parent_formula} vs {aiida_formula}")
            # in the end, use the aiida formula
            parent["formula"] = aiida_formula
    
    db_ids = set()
    cleaned_parents = []
    for i, parent in enumerate(parents):
        # validate each parent. if primary one fails, except. otherwise skip the parent.
        problem = None
        # pydantic validation:
        try:
            Parent3D(**parent)
        except ValidationError as e:
            problem = f"Pydantic: {e.json()}"
        if not problem:
            if parent["source_db_id"] in db_ids:
                problem = "Duplicate"
        if not problem:
            # formula check
            if not get_element_set(parent.get("formula")).issuperset(get_element_set(formula_2d)):
                problem = f"Parent formula not consistent: {parent.get('formula')} vs {formula_2d}"
        
        if problem:
            if i == 0:
                raise ParentsException(f"Primary parent problem: {problem}")
            else:
                log(f"    Warning: non-primary parent: {problem}, skipping {parent}")
                continue
        db_ids.add(parent["source_db_id"])
        cleaned_parents.append(parent)
    
    return cleaned_parents


# only for Mounet dataset:
def query_for_extracted_2d_structure(opt_struct_uuid):
    """
    Using the following insights from looking at the graph about the
    first 2d structure (i.e. the extracted 2d structure):
    * it is (obviously) an ancestor of the optimized one;
    * the CalcFunction that generates it is named "single_lowdimfinder_inline";
    * the edge from the CalcFunction is labelled 'reduced_structure_x'.
    Just return the first such extracted 2d structure (by ctime) (sometimes there are multiple).
    """
    qb = orm.QueryBuilder()
    qb.append(
        orm.StructureData,
        filters={"uuid": opt_struct_uuid},
        tag='opt_struct',
    )
    qb.append(
        orm.StructureData,
        with_descendants="opt_struct",
        tag="extract_struct",
        project="uuid",
    )
    qb.order_by({"extract_struct": {'ctime': 'asc'}})
    qb.append(
        orm.CalcFunctionNode,
        filters={"attributes.function_name": "single_lowdimfinder_inline"},
        with_outgoing="extract_struct",
        edge_filters={'label': {"like": 'reduced\\_structure\\_%'}},
        tag = "extract_fn",
        # project="uuid",
    )
    # note the upper query seems to create many duplicate entries. remove the duplicates:
    unique_results = []
    [unique_results.append(x) for x in qb.all() if x not in unique_results]
    
    # we should have only one "extracted 2d structure"
    if len(unique_results) > 1:
        print(f"Warning: multiple extracted 2d structures - {unique_results}")
    return unique_results[0][0]


def query_band_properties(bands_uuid):
    qb = orm.QueryBuilder()
    qb.append(
        orm.BandsData,
        filters={"uuid": bands_uuid},
        tag="bands",
        project="*",
    )
    qb.append(
        orm.CalcJobNode,
        with_outgoing="bands",
        tag="bands_calc",
    )
    qb.append(
        orm.StructureData,
        with_outgoing="bands_calc",
        tag="struct",
        project="*",
    )
    qb.append(
        orm.Dict,
        filters={'attributes': {'or': [{'has_key': "fermi_energy"}, {'has_key': "fermi_energy_up"}]}},
        with_incoming="bands_calc",
        tag="bands_parameters",
        project="*",
    )
    qb.append(
        orm.CalcFunctionNode,
        with_incoming="bands",
        tag="bandgap_calc",
    )
    qb.append(
        orm.Dict,
        filters={"attributes": {"has_key": "band_gap"}},
        with_incoming="bandgap_calc",
        tag="band_gap",
        project="*"
    )
    results = list(qb.all())

    if len(results) == 0:
        return None

    assert len(results) == 1
    
    _, struct_node, band_out_params_node, band_gap_node = results[0]
    
    fermi_energy = {
        'uuid': band_out_params_node.uuid
    }
    if "fermi_energy" in band_out_params_node.attributes:
        fermi_energy['value'] = [band_out_params_node.attributes["fermi_energy"]]
        
    elif "fermi_energy_up" in band_out_params_node.attributes and "fermi_energy_down" in band_out_params_node.attributes:
        fermi_energy['value'] = [band_out_params_node.attributes["fermi_energy_up"], band_out_params_node.attributes["fermi_energy_down"]]
    
    return {
        "structure": struct_node,
        "band_gap": {
            'uuid': band_gap_node.uuid,
            'value': band_gap_node.attributes["band_gap"] if band_gap_node.attributes["is_insulator"] else 0.0
        },
        "fermi_energy": fermi_energy
    }
