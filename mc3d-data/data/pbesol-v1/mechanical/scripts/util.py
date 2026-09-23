import json
import re
import traceback
from collections.abc import Mapping

from aiida import orm
import numpy as np
import yaml
from aiida.orm import (
    ArrayData,
    BandsData,
    Bool,
    Dict,
    FolderData,
    Group,
    List,
    Node,
    QueryBuilder,
    Str,
    WorkChainNode,
)
from mcxd_web_pipeline.utils import IDS_PATH, get_mc3d_id
from tqdm import tqdm


modulus_pattern = {
    "fd": {
        "elastic_constants": [],
        "Voigt_average": {},
        "Reuss_average": {},
        "VRH_average": {},
    },
    "q0.3": {
        "elastic_constants": [],
        "Voigt_average": {},
        "Reuss_average": {},
        "VRH_average": {},
    },
    "q0.5": {
        "elastic_constants": [],
        "Voigt_average": {},
        "Reuss_average": {},
        "VRH_average": {},
    },
    "q0.7": {
        "elastic_constants": [],
        "Voigt_average": {},
        "Reuss_average": {},
        "VRH_average": {},
    },
}


def count_groups(log=print):
    qb = QueryBuilder().append(Group, project=["*"])
    log(f"{'pk':<10} {'label':<35} {'count':<10}")
    for group in qb.all(flat=True):
        log(f"{group.pk:<10} {group.label:<35} {group.count():<10}")


def count_nodes(node_type, process_type):
    qb = QueryBuilder().append(
        Node, filters={"node_type": node_type, "process_type": process_type}
    )
    return qb.count()


def get_and_count_types():
    qb = QueryBuilder().append(Node, project=["node_type", "process_type"]).distinct()
    print(f"{'count':<10} {'node_type':<50} {'process_type':<10}")
    for [node_type, process_type] in qb.all():
        if process_type:
            count = count_nodes(node_type, process_type)
            print(f"{count:<10} {node_type:<60} {process_type:<60}")
        else:
            count = count_nodes(node_type, None)
            print(f"{count:<10} {node_type:<60} {'None':<60}")


def get_mc3d_versions():
    with IDS_PATH.open("r") as handle:
        mc3d_dict = json.load(handle)
    return set([data["version"] for data in mc3d_dict.values()])


def get_mc3d_id_from_extras(extras, versions=None):
    mc3d_id = None
    if not versions:
        versions = get_mc3d_versions()
    for version in versions:
        source = {
            "id": extras["source_id"],
            "database": extras["source_db"],
            "version": version,
        }
        mc3d_id = get_mc3d_id(source)
        if mc3d_id:
            break
    return mc3d_id


def update_mapping(original, source):
    """Update a nested dictionary with another optionally nested dictionary.

    The dictionaries may be plain Mapping objects or `Dict` nodes. If the original dictionary is an instance of `Dict`
    the returned dictionary will also be wrapped in `Dict`.

    :param original: Mapping object or `Dict` instance
    :param source: Mapping object or `Dict` instance
    :return: the original dictionary updated with the source dictionary
    """
    return_node = False

    if isinstance(original, Dict):
        return_node = True
        original = original.get_dict()

    if isinstance(source, Dict):
        source = source.get_dict()

    for key, value in source.items():
        if (
            key in original
            and isinstance(value, (Dict, Mapping))
            and isinstance(original[key], (Dict, Mapping))
        ):
            original[key] = update_mapping(original[key], value)
        else:
            original[key] = value

    if return_node:
        original = Dict(original)

    return original


def parse_moduli(stdout):
    import re

    results = {"moduli": {}, "sound_velocities": {}, "debye": {}}

    definitions = {
        "voigt": {
            "block_regex": re.compile(
                r"Voigt approximation:\s*([\s\S]*?)(?=\n\s*Reuss approximation:|\Z)"
            ),
            "target_dict": results["moduli"],
            "properties": {
                "bulk_modulus_B": re.compile(r"Bulk modulus\s+B\s*=\s*(-?[\d\.]+)"),
                "young_modulus_E": re.compile(r"Young modulus\s+E\s*=\s*(-?[\d\.]+)"),
                "shear_modulus_G": re.compile(r"Shear modulus\s+G\s*=\s*(-?[\d\.]+)"),
                "poisson_ratio_n": re.compile(r"Poisson Ratio\s+n\s*=\s*(-?[\d\.]+)"),
                "pugh_ratio_r": re.compile(r"Pugh Ratio\s+r\s*=\s*(-?[\d\.]+)"),
            },
        },
        "reuss": {
            "block_regex": re.compile(
                r"Reuss approximation:\s*([\s\S]*?)(?=\n\s*Voigt-Reuss-Hill average|\Z)"
            ),
            "target_dict": results["moduli"],
            "properties": {
                "bulk_modulus_B": re.compile(r"Bulk modulus\s+B\s*=\s*(-?[\d\.]+)"),
                "young_modulus_E": re.compile(r"Young modulus\s+E\s*=\s*(-?[\d\.]+)"),
                "shear_modulus_G": re.compile(r"Shear modulus\s+G\s*=\s*(-?[\d\.]+)"),
                "poisson_ratio_n": re.compile(r"Poisson Ratio\s+n\s*=\s*(-?[\d\.]+)"),
                "pugh_ratio_r": re.compile(r"Pugh Ratio\s+r\s*=\s*(-?[\d\.]+)"),
            },
        },
        "vrh": {
            "block_regex": re.compile(
                r"Voigt-Reuss-Hill average of the two approximations:\s*([\s\S]*?)(?=\n\s*Voigt-Reuss-Hill average; sound velocities:|\Z)"
            ),
            "target_dict": results["moduli"],
            "properties": {
                "bulk_modulus_B": re.compile(r"Bulk modulus\s+B\s*=\s*(-?[\d\.]+)"),
                "young_modulus_E": re.compile(r"Young modulus\s+E\s*=\s*(-?[\d\.]+)"),
                "shear_modulus_G": re.compile(r"Shear modulus\s+G\s*=\s*(-?[\d\.]+)"),
                "longitudinal_modulus_L": re.compile(
                    r"Longitudinal modulus\s+L\s*=\s*(-?[\d\.]+)"
                ),
                "poisson_ratio_n": re.compile(r"Poisson Ratio\s+n\s*=\s*(-?[\d\.]+)"),
                "pugh_ratio_r": re.compile(r"Pugh Ratio\s+r\s*=\s*(-?[\d\.]+)"),
            },
        },
        "velocities": {
            "block_regex": re.compile(
                r"Voigt-Reuss-Hill average; sound velocities:"
                r"\s*([\s\S]*?)(?=\n\s*\+{5,}|\Z)"
            ),
            "target_dict": results,
            "target_key": "sound_velocities",
            "properties": {
                "compressional_V_P": re.compile(
                    r"Compressional\s+V_P\s*=\s*(-?[\d.]+)"
                ),
                "bulk_V_B": re.compile(r"Bulk\s+V_B\s*=\s*(-?[\d.]+)"),
                "shear_V_G": re.compile(r"Shear\s+V_G\s*=\s*(-?[\d.]+)"),
            },
        },
        "debye": {
            "block_regex": re.compile(
                r"(\s*The approximate Debye temperature[\s\S]*?"
                r"Debye temperature\s*=\s*-?[\d.]+\s*K)"
                r"(?=\n\s*\+{5,}|\Z)"
            ),
            "target_dict": results,
            "target_key": "debye",
            "properties": {
                # 'approximate_temperature': re.compile(
                #     r"The approximate Debye temperature\s+is\s+(-?[\d.]+)\s*K"
                # ),
                "average_sound_velocity": re.compile(
                    r"Average Debye sound velocity\s*=\s*(-?[\d.]+)\s*m/s"
                ),
                "temperature": re.compile(
                    r"^\s*Debye temperature\s*=\s*(-?[\d.]+)\s*K", re.MULTILINE
                ),
            },
        },
    }

    for block_name, definition in definitions.items():
        block_match = definition["block_regex"].search(stdout)
        if not block_match:
            continue

        block_text = block_match.group(1)

        # Determine where to store the results for this block
        if "target_key" in definition:
            # For sound_velocities, which is a direct key in results
            storage = definition["target_dict"][definition["target_key"]]
        else:
            # For moduli, which are nested under their block name (voigt, reuss, etc.)
            definition["target_dict"][block_name] = {}
            storage = definition["target_dict"][block_name]

        # Parse properties within the block
        for prop_name, prop_regex in definition["properties"].items():
            prop_match = prop_regex.search(block_text)
            if prop_match:
                storage[prop_name] = float(prop_match.group(1))

    return results


def kbar_to_gpa(modulus):
    for key, value in modulus.items():
        if key in ["bulk_modulus", "young_modulus", "shear_modulus"]:
            modulus[key] = value / 10
    return modulus


def ms_to_kms(sound_velocities):
    for key, value in sound_velocities.items():
        if key in [
            "sound_vel_bulk",
            "sound_vel_shear",
            "sound_vel_compressional",
            "sound_vel_mean",
        ]:
            sound_velocities[key] = value / 1e3
    return sound_velocities


def load_thermo_pw(
    profile,
    label,
    pseudo,
    log=print,
    parser=None,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    thermo_pw_to_matdyn = (
        ("bulk_modulus_B", "bulk_modulus"),
        ("shear_modulus_G", "shear_modulus"),
        ("young_modulus_E", "young_modulus"),
        ("poisson_ratio_n", "poisson_ratio"),
        ("pugh_ratio_r", "pugh_ratio"),
        ("average_sound_velocity", "sound_vel_mean"),
        ("bulk_V_B", "sound_vel_bulk"),
        ("shear_V_G", "sound_vel_shear"),
        ("compressional_V_P", "sound_vel_compressional"),
        ("approximate_temperature", "debye_temp"),
    )

    def rename_modulus(modulus):
        from copy import deepcopy

        new_modulus = deepcopy(modulus)
        for old_key, new_key in thermo_pw_to_matdyn:
            if old_key in new_modulus:
                new_modulus[new_key] = new_modulus.pop(old_key)
        return new_modulus

    qb = orm.QueryBuilder()
    qb.append(orm.Group, filters={"label": label}, tag="thermo_pw_grp").append(
        orm.WorkChainNode,
        with_group="thermo_pw_grp",
        filters={"attributes.exit_status": 0},
        tag="thermo_pw_wc",
    )
    for [workchain_node] in tqdm(qb.iterall(), total=qb.count()):
        structure = workchain_node.inputs.thermo_pw.structure
        extras = structure.base.extras.all
        source = f"{extras['source_db']}-{extras['source_id']}"
        try:
            if "source_db" not in workchain_node.base.extras.all:
                extras = structure.base.extras.all
            else:
                extras = workchain_node.base.extras.all

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {workchain_node.pk} {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue

            details_entry = {mc3d_id: {"elastic": {"FD": {pseudo: {}}}}}
            details_entry[mc3d_id]["elastic"]["FD"][pseudo]["pseudo"] = (
                "PBE" if pseudo == "PseudoDojo" else "PBEsol"
            )
            details_entry[mc3d_id]["elastic"]["FD"][pseudo]["structure_uuid"] = (
                structure.uuid
            )
            details_entry[mc3d_id]["elastic"]["FD"][pseudo]["workchain_uuid"] = (
                workchain_node.uuid
            )
            details_entry[mc3d_id]["elastic"]["FD"][pseudo]["scf_parameters_uuid"] = (
                workchain_node.inputs.thermo_pw.parameters.uuid
            )
            details_entry[mc3d_id]["elastic"]["FD"][pseudo]["scf_kpoints_uuid"] = (
                workchain_node.base.links.get_outgoing(link_label_filter="iteration_01")
                .first()
                .node.inputs.kpoints.uuid
            )

            elastic_constants = workchain_node.outputs.elastic_constants.get_array(
                "elastic_constants"
            )

            if parser:
                output_parameters = parser(
                    workchain_node.outputs.retrieved.get_object_content("aiida.out")
                )
            else:
                output_parameters = workchain_node.outputs.output_parameters.get_dict()
            try:
                details_entry[mc3d_id]["elastic"]["FD"][pseudo]["elastic_constants"] = (
                    elastic_constants / 10
                ).tolist()
                details_entry[mc3d_id]["elastic"]["FD"][pseudo]["Voigt_average"] = (
                    kbar_to_gpa(rename_modulus(output_parameters["moduli"]["voigt"]))
                )
                details_entry[mc3d_id]["elastic"]["FD"][pseudo]["Reuss_average"] = (
                    kbar_to_gpa(rename_modulus(output_parameters["moduli"]["reuss"]))
                )
                details_entry[mc3d_id]["elastic"]["FD"][pseudo]["VRH_average"] = (
                    kbar_to_gpa(rename_modulus(output_parameters["moduli"]["vrh"]))
                )
                details_entry[mc3d_id]["elastic"]["FD"][pseudo]["sound_velocities"] = (
                    ms_to_kms(rename_modulus(output_parameters["sound_velocities"]))
                )
                details_entry[mc3d_id]["elastic"]["FD"][pseudo]["debye"] = ms_to_kms(
                    rename_modulus(output_parameters["debye"])
                )

                for average in ["Voigt_average", "Reuss_average", "VRH_average"]:
                    bulk_modulus = details_entry[mc3d_id]["elastic"]["FD"][pseudo][
                        average
                    ]["bulk_modulus"]
                    young_modulus = details_entry[mc3d_id]["elastic"]["FD"][pseudo][
                        average
                    ]["young_modulus"]
                    pettifor_ratio = (
                        (elastic_constants[0][1] - elastic_constants[3][3])
                        / 10
                        / young_modulus
                    )
                    modified_pettifor_ratio = (
                        (elastic_constants[0][1] - elastic_constants[3][3])
                        / 10
                        / bulk_modulus
                    )
                    details_entry[mc3d_id]["elastic"]["FD"][pseudo][average][
                        "pettifor_ratio"
                    ] = pettifor_ratio
                    details_entry[mc3d_id]["elastic"]["FD"][pseudo][average][
                        "modified_pettifor_ratio"
                    ] = modified_pettifor_ratio
            except Exception as e:
                print(f"Error processing {source}[{workchain_node.pk}]: {e}")
                pass
            details = update_mapping(details, details_entry)

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def load_matdyn(
    profile,
    label,
    pseudo,
    qdensity,
    log=print,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    qb = orm.QueryBuilder()
    qb.append(orm.Group, filters={"label": label}, tag="matdyn_grp").append(
        orm.WorkChainNode,
        with_group="matdyn_grp",
        filters={
            "attributes.exit_status": 0,
            "attributes.process_label": "MatdynBaseWorkChain",
        },
        tag="matdyn_wc",
    )

    for [workchain_node] in tqdm(qb.iterall(), total=qb.count()):
        extras = workchain_node.base.extras.all

        # structure = workchain_node.inputs.thermo_pw.structure
        # extras = structure.base.extras.all
        source = f"{extras['source_db']}-{extras['source_id']}"
        try:
            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {workchain_node.pk} {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue

            details_entry = {mc3d_id: {"elastic": {"Born": {pseudo: {qdensity: {}}}}}}

            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity]["pseudo"] = (
                "PBE" if pseudo == "PseudoDojo" else "PBEsol"
            )
            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "workchain_uuid"
            ] = workchain_node.uuid
            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "scf_parameters_uuid"
            ] = workchain_node.inputs.matdyn.force_constants.creator.inputs.parent_folder.creator.caller.inputs.ph.parent_folder.creator.inputs.parameters.uuid
            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "scf_kpoints_uuid"
            ] = workchain_node.inputs.matdyn.force_constants.creator.inputs.parent_folder.creator.caller.inputs.ph.parent_folder.creator.inputs.kpoints.uuid
            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "qpoints_uuid"
            ] = workchain_node.inputs.matdyn.force_constants.creator.inputs.parent_folder.creator.inputs.qpoints.uuid

            # The output ports of MatdynCalculation are actually exposed to MatdynBaseWorkChain but sometimes
            # it is not, so we need to find the actual MatdynCalculation node.
            # This could be a bug inside aiida
            # The MatdynBaseWorkChain has a link named "iteration_01" to the MatdynCalculation node

            if "output_elastic_properties" in workchain_node.outputs._get_keys():
                output_elastic_properties = (
                    workchain_node.outputs.output_elastic_properties
                )

            else:
                calculation_node = (
                    workchain_node.base.links.get_outgoing(
                        link_label_filter="iteration_01"
                    )
                    .first()
                    .node
                )

                if "output_elastic_properties" in calculation_node.outputs._get_keys():
                    output_elastic_properties = (
                        calculation_node.outputs.output_elastic_properties
                    )
                else:
                    # log(f"DEBUG: output_elastic_properties not found in calculation node {calculation_node.pk}")
                    matdyn_elastic_yaml = (
                        calculation_node.outputs.retrieved.get_object_content(
                            "matdyn.elastic.yaml"
                        )
                    )
                    output_elastic_properties = yaml.safe_load(matdyn_elastic_yaml)

            elastic_constants = np.array(
                output_elastic_properties.get("elastic_constants")
            )
            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "elastic_constants"
            ] = elastic_constants.tolist()

            # details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity]['qpoints_uuid'] = workchain_node.inputs.matdyn.force_constants.creator.inputs.parent_folder.creator.inputs.qpoints.uuid
            # details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity]['scf_parameters_uuid'] = workchain_node.inputs.matdyn.force_constants.creator.inputs.parent_folder.creator.inputs.parent_folder.creator.inputs.parameters.uuid
            # details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity]['scf_kpoints_uuid'] = workchain_node.inputs.matdyn.force_constants.creator.inputs.parent_folder.creator.inputs.parent_folder.creator.inputs.kpoints.uuid

            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "Voigt_average"
            ] = output_elastic_properties.get("Voigt_average")
            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "Reuss_average"
            ] = output_elastic_properties.get("Reuss_average")
            details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                "VRH_average"
            ] = output_elastic_properties.get("VRH_average")
            for average in ["Voigt_average", "Reuss_average", "VRH_average"]:
                bulk_modulus = details_entry[mc3d_id]["elastic"]["Born"][pseudo][
                    qdensity
                ][average]["bulk_modulus"]
                young_modulus = details_entry[mc3d_id]["elastic"]["Born"][pseudo][
                    qdensity
                ][average]["young_modulus"]
                pettifor_ratio = (
                    elastic_constants[0][1] - elastic_constants[3][3]
                ) / young_modulus
                modified_pettifor_ratio = (
                    elastic_constants[0][1] - elastic_constants[3][3]
                ) / bulk_modulus
                pugh_ratio = (
                    1
                    / details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][
                        average
                    ]["pugh_ratio"]
                )
                details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][average][
                    "pugh_ratio"
                ] = pugh_ratio
                details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][average][
                    "pettifor_ratio"
                ] = pettifor_ratio
                details_entry[mc3d_id]["elastic"]["Born"][pseudo][qdensity][average][
                    "modified_pettifor_ratio"
                ] = modified_pettifor_ratio
            details = update_mapping(details, details_entry)

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def calculate_iso_tc(max_eigenvalue):
    from scipy.interpolate import interp1d

    me_array = max_eigenvalue.get_array("max_eigenvalue")
    if me_array[:, 1].max() < 1.0:
        return 0.0
    else:
        return float(interp1d(me_array[:, 1], me_array[:, 0])(1.0))


def calculate_Allen_Dynes_tc(a2f, mustar=0.13):
    import numpy

    w = a2f.get_array("frequency")
    # Here we preassume that there are 10 smearing values for a2f calculation
    spectral = a2f.get_array("a2f")[:, 9]
    mev2K = 11.604525006157

    _lambda = 2 * numpy.trapz(numpy.divide(spectral, w), x=w)

    # wlog =  np.exp(np.average(np.divide(alpha, w), weights=np.log(w)))
    wlog = numpy.exp(
        2
        / _lambda
        * numpy.trapz(numpy.multiply(numpy.divide(spectral, w), numpy.log(w)), x=w)
    )

    denominator = _lambda - mustar * (1 + 0.62 * _lambda)
    if denominator < 0:
        Tc = 0.0
    else:
        Tc = wlog / 1.2 * numpy.exp(-1.04 * (1 + _lambda) / denominator) * mev2K

    return (wlog, _lambda, Tc)


def load_scon(
    profile,
    label,
    log=print,
    details={},
):

    count_successful = 0
    count_skipped = 0

    from aiida import orm, load_profile

    load_profile(profile, allow_switch=True)

    qb_scon = (
        orm.QueryBuilder()
        .append(
            orm.Group,
            filters={"label": label},
            tag="scon_group",
        )
        .append(
            orm.WorkChainNode,
            project=["*"],
            tag="scon_wc",
            with_group="scon_group",
            filters={"attributes.exit_status": 0},
        )
        .append(
            orm.XyData,
            project=["*"],
            with_incoming="scon_wc",
            edge_filters={"label": "max_eigenvalue"},
        )
        .append(
            orm.ArrayData,
            project=["*"],
            with_incoming="scon_wc",
            edge_filters={"label": "a2f"},
        )
    )

    for workchain_node, max_eigenvalue, a2f in tqdm(
        qb_scon.iterall(), total=qb_scon.count()
    ):
        try:
            structure = workchain_node.inputs.structure

            if "source_db" not in workchain_node.base.extras.all:
                extras = workchain_node.inputs.structure.base.extras.all
            else:
                extras = workchain_node.base.extras.all

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {workchain_node.pk} {extras}")
                count_skipped += 1
                continue

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {workchain_node.pk} {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue
            details_entry = {}

            wlog, _lambda, allen_dynes_tc = calculate_Allen_Dynes_tc(a2f)
            iso_tc = calculate_iso_tc(max_eigenvalue)

            details_entry["iso_tc"] = iso_tc
            details_entry["allen_dynes_tc"] = allen_dynes_tc

            if mc3d_id in details:
                details[mc3d_id]["elastic"]["FD"]["PseudoDojo"].update(details_entry)
            else:
                details[mc3d_id]["elastic"]["FD"]["PseudoDojo"] = details_entry

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {mc3d_id}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue

    return count_successful


def calculate_c(details, log=print):
    """Calculate and add the Pugh--Pettifor superconducting descriptor.

    The descriptor is evaluated separately for the Voigt, Reuss, and VRH
    elastic averages and stored as ``c`` in the corresponding average mapping:

    ``c = iso_tc / mean(iso_tc) + pettifor_ratio / mean(pettifor_ratio)
    - pugh_ratio / mean(pugh_ratio)``.

    Only entries containing all three finite values for a given average are
    included in that average's reference means and receive a descriptor value.
    ``details`` is updated in place and returned for convenience.
    """
    averages = ("Voigt_average", "Reuss_average", "VRH_average")
    values_by_average = {average: [] for average in averages}

    for mc3d_id, detail in details.items():
        try:
            fd_pseudodojo = detail["elastic"]["FD"]["PseudoDojo"]
            iso_tc = float(fd_pseudodojo["iso_tc"])
        except (KeyError, TypeError, ValueError):
            continue

        for average in averages:
            try:
                elastic_average = fd_pseudodojo[average]
                modified_pettifor_ratio = float(
                    elastic_average["modified_pettifor_ratio"]
                )
                pugh_ratio = float(elastic_average["pugh_ratio"])
            except (KeyError, TypeError, ValueError):
                continue

            if np.isfinite((iso_tc, modified_pettifor_ratio, pugh_ratio)).all():
                values_by_average[average].append(
                    (
                        mc3d_id,
                        elastic_average,
                        iso_tc,
                        modified_pettifor_ratio,
                        pugh_ratio,
                    )
                )

    for average, values in values_by_average.items():
        if not values:
            continue

        iso_tc_average = np.mean([value[2] for value in values])
        modified_pettifor_average = np.mean([value[3] for value in values])
        pugh_average = np.mean([value[4] for value in values])

        log(
            f"average of {len(values)} isotropic Tc: {iso_tc_average}, "
            f"average of {average} {len(values)} pettifor ratio: {modified_pettifor_average}, "
            f"average of {average} {len(values)} pugh ratio: {pugh_average}"
        )

        if np.isclose(
            (iso_tc_average, modified_pettifor_average, pugh_average), 0.0
        ).any():
            log(
                f"SKIPPING c calculation for {average}: "
                "at least one reference average is zero."
            )
            continue

        for _, elastic_average, iso_tc, modified_pettifor_ratio, pugh_ratio in values:
            elastic_average["c"] = float(
                iso_tc / iso_tc_average
                + modified_pettifor_ratio / modified_pettifor_average
                - pugh_ratio / pugh_average
            )

    return details


def aggregate_recursive(source, target):
    """
    According to the structure of target, count how many times
    each target leaf key appears in source.

    对于 target 中的叶子节点：
    无论 source 中对应的值是数字、列表还是字典，都只计数一次。
    """
    if not isinstance(source, dict):
        return target

    for key in target:
        # source 中没有这个字段，不计数
        if key not in source:
            continue

        target_value = target[key]
        source_value = source[key]

        # target 中是字典，说明这一层属于统计路径，需要继续递归
        if isinstance(target_value, dict):
            if isinstance(source_value, dict):
                aggregate_recursive(source_value, target_value)

        # target 中是整数，说明这是需要统计的最终字段
        else:
            target[key] += 1

    return target


def check_base_json(details, log=print):
    statistics = {
        "elastic": {
            "Born": {
                "SSSP": {
                    "0.7": {
                        "VRH_average": 0,
                        "elastic_constants": 0,
                        "Reuss_average": 0,
                        "Voigt_average": 0,
                        "workchain_uuid": 0,
                    },
                    "0.5": {
                        "VRH_average": 0,
                        "elastic_constants": 0,
                        "Reuss_average": 0,
                        "Voigt_average": 0,
                        "workchain_uuid": 0,
                    },
                    "0.3": {
                        "VRH_average": 0,
                        "elastic_constants": 0,
                        "Reuss_average": 0,
                        "Voigt_average": 0,
                        "workchain_uuid": 0,
                    },
                },
                "PseudoDojo": {
                    "0.5": {
                        "VRH_average": 0,
                        "elastic_constants": 0,
                        "Reuss_average": 0,
                        "Voigt_average": 0,
                        "workchain_uuid": 0,
                    }
                },
            },
            "FD": {
                "SSSP": {
                    "VRH_average": 0,
                    "elastic_constants": 0,
                    "Reuss_average": 0,
                    "structure_uuid": 0,
                    "Voigt_average": 0,
                },
                "PseudoDojo": {
                    "iso_tc": 0,
                    "allen_dynes_tc": 0,
                    "VRH_average": 0,
                    "elastic_constants": 0,
                    "Reuss_average": 0,
                    "structure_uuid": 0,
                    "Voigt_average": 0,
                },
            },
        }
    }

    for detail in details.values():
        aggregate_recursive(detail, statistics)

    log_statistics(statistics, log=log)

    return statistics


def log_statistics(node, log=print, indent=0):
    """
    Recursively print all leaf counts.
    """
    for key, value in node.items():
        prefix = " " * indent

        if isinstance(value, dict):
            log(f"{prefix}{key}:")
            log_statistics(value, log=log, indent=indent + 2)
        else:
            log(f"{prefix}{key:38s}: {value:5d}")


def compare(dict1, dict2, sources=None):
    shared_sources = dict1.keys() & dict2.keys()
    if sources:
        shared_sources = set(sources) & shared_sources

    compare_dict = {
        "sources": [],
        "elastic_constants": [],
        "Voigt_average": {
            "bulk_modulus": [],
            "shear_modulus": [],
            "young_modulus": [],
            "poisson_ratio": [],
            "pugh_ratio": [],
            "pettifor_ratio": [],
            "modified_pettifor_ratio": [],
        },
        "Reuss_average": {
            "bulk_modulus": [],
            "shear_modulus": [],
            "young_modulus": [],
            "poisson_ratio": [],
            "pugh_ratio": [],
            "pettifor_ratio": [],
            "modified_pettifor_ratio": [],
        },
        "VRH_average": {
            "bulk_modulus": [],
            "shear_modulus": [],
            "young_modulus": [],
            "poisson_ratio": [],
            "pugh_ratio": [],
            "pettifor_ratio": [],
            "modified_pettifor_ratio": [],
        },
    }
    for source in shared_sources:
        compare_dict["sources"].append(source)
        compare_dict["elastic_constants"].append(
            [dict1[source]["elastic_constants"], dict2[source]["elastic_constants"]]
        )
        for average in ["Voigt_average", "Reuss_average", "VRH_average"]:
            for modulus in [
                "bulk_modulus",
                "shear_modulus",
                "young_modulus",
                "poisson_ratio",
                "pugh_ratio",
                "pettifor_ratio",
                "modified_pettifor_ratio",
            ]:
                try:
                    if modulus not in compare_dict[average]:
                        continue

                    compare_dict[average][modulus].append(
                        [
                            dict1[source][average][modulus],
                            dict2[source][average][modulus],
                        ]
                    )
                except Exception as e:
                    print(f"Error processing {source}'s {average} {modulus}: {e}")
                    pass

            # compare_dict[average]['pettifor_ratio'].append(
            #     [(dict1[source]['elastic_constants'][0][1] - dict1[source]['elastic_constants'][3][3]) / dict1[source][average]['young_modulus'],
            #      (dict2[source]['elastic_constants'][0][1] - dict2[source]['elastic_constants'][3][1]) / dict2[source][average]['young_modulus']
            #      ]
            # )
            # compare_dict[average]['modified_pettifor_ratio'].append(
            #     [(dict1[source]['elastic_constants'][0][1] - dict1[source]['elastic_constants'][3][3]) / dict1[source][average]['bulk_modulus'],
            #      (dict2[source]['elastic_constants'][0][1] - dict2[source]['elastic_constants'][3][1]) / dict2[source][average]['bulk_modulus']
            #      ]
            # )
    return compare_dict


def converge(dict1, dict2, threshold=0.05):
    converged = []
    sources = dict1.keys() & dict2.keys()
    for source in sources:
        for average in dict1[source].keys():
            if average == "elastic_constants":
                continue
            for (modulus, value1), (_, value2) in zip(
                dict1[source][average].items(), dict2[source][average].items()
            ):
                if modulus not in [
                    "bulk_modulus",
                    "shear_modulus",
                    "young_modulus",
                    "poisson_ratio",
                    "pugh_ratio",
                    "pettifor_ratio",
                    "modified_pettifor_ratio",
                ]:
                    continue
                if abs((value1 - value2) / value1) < threshold:
                    converged.append((source, average, modulus))
    return converged


def converged_average_modulus(converged, average, modulus):
    return [
        source
        for (source, _average, _modulus) in converged
        if average == _average and modulus == _modulus
    ]


def exclude_sources(dict, sources):
    filtered_dict = {}
    for source in dict.keys():
        if source in sources:
            filtered_dict[source] = dict[source]
    return filtered_dict


def get_sources(profile, group_label, check_stability=True):
    sources = []

    import aiida

    aiida.load_profile(profile, allow_switch=True)

    qb = orm.QueryBuilder()
    qb.append(orm.Group, filters={"label": group_label}, tag="group").append(
        orm.WorkChainNode,
        with_group="group",
    )
    for workchain in qb.all(flat=True):
        extras = workchain.base.extras.all
        if check_stability:
            is_stable, _ = check_stability_matdyn_base(workchain)
            if not is_stable:
                continue
        sources.append(f"{extras['source_db']}-{extras['source_id']}")

    return sources


def find_max_value_and_path(data):
    """
    Traverse a multi-layer dictionary to find the maximum value and its path.

    :param data: The input multi-layer dictionary.
    :return: A tuple containing (key path list, maximum value), or None if no numeric values are found.
    """

    max_value = None
    max_path = None

    # Traverse the dictionary
    for key, value in data.items():
        current_path = [key]  # The path segment of the current node

        if isinstance(value, dict):
            # 1. Recursive case: If the value is a dictionary, continue to explore downwards

            # Recursively call itself to get the maximum value and path in the subtree
            recursive_result = find_max_value_and_path(value)

            if recursive_result is not None:
                sub_path, sub_value = recursive_result

                # Combine paths: current key + sub-path
                full_path = current_path + sub_path

                # Update the global maximum value
                if max_value is None or sub_value > max_value:
                    max_value = sub_value
                    max_path = full_path

        elif isinstance(value, (int, float)):
            # 2. Basic case: If the value is a number, compare directly

            if max_value is None or value > max_value:
                max_value = value
                max_path = current_path

    # Return the maximum value and path found in the current dictionary
    if max_path is not None:
        return (max_path, max_value)
    else:
        # If the dictionary does not contain any numeric values (e.g., only empty dictionaries or non-numeric strings)
        return None


def check_stability_matdyn_base(
    workchain: orm.WorkChainNode,
    tolerance: float = -5.0,  # cm^{-1}
) -> tuple[bool, str]:
    """Check if the matdyn.x interpolated phonon band structure is stable."""
    THZ_TO_CM = 33.356
    bands = workchain.outputs.output_phonon_bands.get_bands() * THZ_TO_CM  # unit: THz
    min_freq = np.min(bands)
    if min_freq < tolerance:
        return (
            False,
            f"The phonon from `matdyn_base` is unstable.\nWith the minimum frequency {min_freq:.2f} cm^{-1}.",
        )
    else:
        return (
            True,
            f"The phonon from `matdyn_base` is stable, with the minimum frequency {min_freq:.2f} cm^{-1}.",
        )


def compare_two_keys(dict, key1, key2):
    values = {
        "Voigt_average": [],
        "Reuss_average": [],
        "VRH_average": [],
    }
    for source in dict.keys():
        for average in ["Voigt_average", "Reuss_average", "VRH_average"]:
            try:
                values[average].append(
                    [dict[source][average][key1], dict[source][average][key2]]
                )
            except:
                print("Error in source: ", source)
    return values
