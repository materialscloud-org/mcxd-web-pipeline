import json
import math
from pathlib import Path

from aiida import orm
from aiida_quantumespresso.utils.validation.trajectory import (
    verify_convergence_trajectory,
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent

IDS_PATH = PACKAGE_ROOT.parent / "mc3d-data" / "ids" / "mc3d-ids.json"

# Define load IDs when this module is imported:
with IDS_PATH.open("r") as handle:
    mc3d_dict = json.load(handle)
    inv_mc3d_dict = {
        (data['id'], data['database']): mc3d_id for mc3d_id, data in mc3d_dict.items()
    }


def get_mc3d_id(source):
    try:
        return inv_mc3d_dict[
            (
                source["id"],
                # source["version"],
                source["database"],
            )
        ]
    except KeyError:
        return None


def get_base_details_entry(structure_node, property_dict_list):
    """
    Get the base MC details entry from the relaxed structure and from property parameters.

    property_dict_list - List of Dict nodes which is checked for property keys.
    """
    extras = structure_node.extras

    # get the pymatgen iupac reduced formula:
    pmg_formula = structure_node.get_pymatgen_structure().composition.reduced_formula
    # full hill formula:
    hill_formula = structure_node.get_formula(mode="hill")

    properties = {}

    PROP_KEY_ALIASES = {
        "total_energy": ["energy"],
        "cell_volume": ["volume"],
    }

    for property_node in property_dict_list:
        params = property_node.get_dict()
        for key in [
            "total_energy",
            "cell_volume",
            "total_magnetization",
            "absolute_magnetization",
        ]:
            for alias in [key] + PROP_KEY_ALIASES.get(key, []):
                if alias in params:
                    properties[key] = {
                        "value": round(params[alias], 4),
                        "uuid": property_node.uuid,
                    }

    if "info" not in extras["source"]:
        raise ValueError(
            "Missing source.info extra, please run the corresponding script to add this data."
        )

    return {
        "general": {
            "structure_uuid": structure_node.uuid,
            "bravais_lattice": extras["bravais_lattice"],
            "formula": pmg_formula,
            "formula_hill": hill_formula,
            "spacegroup_international": extras["spacegroup_international"],
            "spacegroup_number": extras["spacegroup_number"],
        },
        "source": [
            {
                "database": extras["source"].get("database").upper(),
                "id": extras["source"].get("id"),
                "version": extras["source"].get("version"),
                "info": extras["source"].get("info"),
            }
        ],
        "properties": properties,
    }


def count_aiida_node_types():
    """
    Return all AiiDA node types and their counts
    """

    def count_nodes(node_type, process_type):
        qb = orm.QueryBuilder().append(
            orm.Node, filters={"node_type": node_type, "process_type": process_type}
        )
        return qb.count()

    qb = (
        orm.QueryBuilder()
        .append(orm.Node, project=["node_type", "process_type"])
        .distinct()
    )

    for entry in qb.all():
        print(count_nodes(entry[0], entry[1]), entry[0], entry[1])


def verify_optimization_convergence(trajectory):
    is_converged = verify_convergence_trajectory(
        trajectory, threshold_forces=0.01, threshold_stress=5
    )
    if not is_converged:
        return False
    is_converged_tight = verify_convergence_trajectory(
        trajectory, threshold_forces=0.0001, threshold_stress=0.5
    )
    if is_converged_tight:
        return "tight"

    return "standard"


### "Canonical" json ###


def _round_sig_or_dec(x: float, prec: int = 8) -> float:
    """Round to significant digits for small numbers, decimal digits for large ones."""
    if x == 0 or math.isnan(x) or math.isinf(x):
        return x

    magnitude = abs(x)

    if magnitude >= 1:
        # Round by decimal digits
        return round(x, prec)
    else:
        # Round by significant digits
        return round(x, prec - int(math.floor(math.log10(magnitude))) - 1)


def _normalize(obj, prec: int = 8):
    """Recursively normalize floats and sort keys."""
    if isinstance(obj, float):
        return _round_sig_or_dec(obj, prec)
    elif isinstance(obj, dict):
        return {
            k: _normalize(v, prec)
            for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))
        }
    elif isinstance(obj, (list, tuple)):
        return [_normalize(v, prec) for v in obj]
    return obj


def dumps_canonical_json(data, prec: int = 8) -> str:
    """Return canonical JSON string with rounded floats and sorted keys."""
    normalized = _normalize(data, prec)
    return json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
    )


def dump_canonical_json(data, fp, prec: int = 8):
    """Write canonical JSON to a file-like object."""
    fp.write(dumps_canonical_json(data, prec=prec))
    fp.write("\n")
