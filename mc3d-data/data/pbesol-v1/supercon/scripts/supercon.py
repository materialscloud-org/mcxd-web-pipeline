import json
import re
import traceback
from collections.abc import Mapping

import numpy
from aiida.engine import calcfunction
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
from aiida.tools.data.array.kpoints.main import get_explicit_kpoints_path
from ase.spacegroup.symmetrize import check_symmetry
from mcxd_web_pipeline.utils import IDS_PATH, get_mc3d_id
from tqdm import tqdm

THZ_TO_MEV = 4.14


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


def find_average(data, T):
    import numpy as np

    data = data[data[:, 1] >= 0]

    T = float(T)

    midpoint = np.average(data[:, 1], weights=data[:, 0] - T)
    return midpoint


def plot_a2f(
    a2f,
    axis=None,
    **kwargs,
    ):
    w = a2f.get_array("frequency")
    spectral = a2f.get_array("a2f")

    if axis is None:
        from matplotlib import pyplot as plt

        fig, ax = plt.subplots()
    else:
        ax = axis

    ax.plot(
        spectral[:, 9],
        w,
        color=kwargs.get("color", "r"),
        linestyle=kwargs.get("linestyle", "-"),
        label=r"$\alpha^2F$",
    )
    ax.plot(
        spectral[:, 19],
        w,
        color=kwargs.get("color", "k"),
        linestyle=kwargs.get("linestyle", "--"),
        label=r"$\lambda$",
    )
    ax.set_xticks(
        [0, round(numpy.max(spectral[:, [9, 19]]) * 1.05, 1)],
        [0, round(numpy.max(spectral[:, [9, 19]]) * 1.05, 1)],
    )
    ax.set_yticks(
        [0, round(numpy.max(w) * 1.05, 1)],
        [0, round(numpy.max(w) * 1.05, 1)],
    )
    ax.set_xlim(0, round(numpy.max(spectral[:, [9, 19]]) * 1.05, 1))
    ax.set_ylim(0, round(numpy.max(w) * 1.05, 1))
    # ax.set_ylabel(r"$\alpha^2F$")
    ax.set_ylabel(r"$\omega$ [meV]")

    if axis is None:
        return plt


def plot_gap_function(
    retrieved,
    ax,
    remove_temps=[0, 0],
    prefix="aiida",
    suggested_p=None,
    exclude_points=None,
    verbose=False,
):
    from io import StringIO

    import numpy as np
    from scipy.optimize import curve_fit

    def fitting_function(T, p, delta_zero, Tc):
        return delta_zero * (1 - (T / Tc) ** p) ** 0.5

    rhos = []
    temps = []
    average_deltas = []

    for filename in retrieved.list_object_names():
        if filename.startswith(f"{prefix}.imag_aniso_gap0_"):
            if verbose:
                print(f"Reading {filename}")
            text = retrieved.base.repository.get_object_content(filename)
        else:
            continue
        parse = np.loadtxt(StringIO(text))
        try:
            temp = parse[:, 0]
            delta_nk = parse[:, 1]

            if len(temp) <= 2:
                continue
            mid = find_average(parse, min(temp))

            temps.append(min(temp))
            average_deltas.append(mid)
            rhos.append(parse)

        except IndexError:
            continue
    if verbose:
        print(f"temps: {temps}")
        print(f"average_deltas: {average_deltas}")

    ntemps = len(temps)
    if ntemps <= 2:
        raise ValueError("less than 2 temperature, can't be fit")

    _, sorted_rhos = zip(*sorted(zip(temps, rhos)))

    sorted_pairs = sorted(zip(temps, average_deltas), key=lambda x: x[0])
    temps_sorted, average_deltas_sorted = zip(*sorted_pairs)

    if exclude_points is not None:
        temps_sorted = [
            temps_sorted[i] for i in range(ntemps) if i not in exclude_points
        ]
        average_deltas_sorted = [
            average_deltas_sorted[i] for i in range(ntemps) if i not in exclude_points
        ]
        sorted_rhos = [sorted_rhos[i] for i in range(ntemps) if i not in exclude_points]

        ntemps -= len(exclude_points)

    well_fit = False
    if ntemps == 3:
        if suggested_p is not None:
            p = suggested_p
        else:
            p = [1, average_deltas[0], max(temps)]
        if verbose:
            print(f"Using initial guess: {p}")
        p_opt, p_cov = curve_fit(
            fitting_function, temps_sorted, average_deltas_sorted, p0=p, maxfev=1000000
        )
        diff = fitting_function(temps_sorted, *p_opt) - average_deltas_sorted
        well_fit = True

    else:
        if suggested_p is not None:
            p = suggested_p
        else:
            p = [1, average_deltas[0], temps_sorted[ntemps - remove_temps[1] - 1]]
        if verbose:
            print(f"Using initial guess: {p}")
        try:
            p_opt, p_cov = curve_fit(
                fitting_function,
                temps_sorted[remove_temps[0] : ntemps - remove_temps[1]],
                average_deltas_sorted[remove_temps[0] : ntemps - remove_temps[1]],
                p0=p,
                maxfev=1000000,
            )
            diff = (
                fitting_function(
                    temps_sorted[remove_temps[0] : ntemps - remove_temps[1]], *p_opt
                )
                - average_deltas_sorted[remove_temps[0] : ntemps - remove_temps[1]]
            )
            if (
                np.linalg.norm(p_cov) < 10
                or (ntemps - remove_temps[0] - remove_temps[1]) == 3
            ):
                well_fit = True
        except:
            print("Curve fit failed")

    if verbose:
        print(f"Anisotropic gap fit: {well_fit}")

    if well_fit:
        final_tems = temps_sorted[remove_temps[0] : ntemps - remove_temps[1]]
        final_rhos = sorted_rhos[remove_temps[0] : ntemps - remove_temps[1]]

        width_and_incre = []
        for idr, rho in enumerate(final_rhos[:-1]):
            width_of_rho = np.max(rho[:, 0]) - final_tems[idr]
            incre_of_tem = final_tems[idr + 1] - final_tems[idr]

            width_and_incre.append([width_of_rho / incre_of_tem])

        max_ratio = np.max(width_and_incre)
        if max_ratio > 1:
            suppression = 0.9 / max_ratio
        else:
            suppression = 1

        max_rho = 0
        if ax:
            for T, rho in zip(
                temps_sorted[remove_temps[0] : ntemps - remove_temps[1]],
                sorted_rhos[remove_temps[0] : ntemps - remove_temps[1]],
            ):
                ax.axvline(np.min(rho[:, 0]), color="k", linestyle="-", linewidth=1.5)
                ax.plot(
                    T + suppression * (rho[:, 0] - T),
                    rho[:, 1],
                    color="black",
                    linewidth=1.5,
                )
                max_rho = np.max([np.max(rho[:, 1]), max_rho])

            ax.scatter(
                temps_sorted[remove_temps[0] : ntemps - remove_temps[1]],
                average_deltas_sorted[remove_temps[0] : ntemps - remove_temps[1]],
                c="r",
                s=70,
            )
            ax.set_xlabel("$T$ [K]", fontsize=20)
            ax.set_ylabel("$\Delta_{nk}$ [meV]", fontsize=20)

            x_fit = np.linspace(np.min(temps) * 0.7, p_opt[-1] - 0.0001, 1000)
            y_fit = fitting_function(x_fit, *p_opt)

            ax.plot(
                x_fit,
                y_fit,
                color="red",
                linestyle="--",
                linewidth=1.5,
            )

            ax.set_xlim([np.min(temps) * 0.8, np.round(p_opt[-1] * 1.2, decimals=0)])
            ax.set_ylim([0, max_rho])
            ax.set_xticks(
                [
                    np.round(np.min(temps) * 0.8, decimals=0),
                    np.round(p_opt[-1] * 1.2, decimals=0),
                ],
                [
                    np.round(np.min(temps) * 0.8, decimals=0),
                    np.round(p_opt[-1] * 1.2, decimals=0),
                ],
                fontsize=20,
            )

            ax.set_yticks(
                [0.0, np.round(p_opt[1] * 1.3, decimals=0)],
                [0.0, np.round(p_opt[1] * 1.3, decimals=0)],
                fontsize=20,
            )

        return {
            # 'n_points': ntemps,
            # 'point_to_remove': remove_temps,
            "temps": temps_sorted[remove_temps[0] : ntemps - remove_temps[1]],
            # 'rhos': sorted_rhos[remove_temps[0]:ntemps-remove_temps[1]],
            "average_deltas": average_deltas_sorted[
                remove_temps[0] : ntemps - remove_temps[1]
            ],
            # "p_cov": p_cov,
            "Tc": p_opt[2],
            "delta0": p_opt[1],
            "expo": p_opt[0],
        }

    else:
        return None


def plot_gap_function_arraydata(
    gap_functions,
    ax=None,
    p_opt=None,
):
    import numpy as np
    from scipy.optimize import curve_fit

    def fitting_function(T, p, delta_zero, Tc):
        return delta_zero * (1 - (T / Tc) ** p) ** 0.5

    temps_sorted = []
    average_deltas_sorted = []
    rhos_sorted = []

    for _, arr in gap_functions.get_iterarrays():
        T = np.min(arr[:, 0])
        temps_sorted.append(T)
        average_deltas_sorted.append(np.average(arr[:, 1], weights=arr[:, 0] - T))
        rhos_sorted.append(arr)

    if p_opt is not None:
        p = p_opt
    else:
        p = [1, average_deltas_sorted[0], temps_sorted[-1]]

    width_and_incre = []
    for idr, rho in enumerate(rhos_sorted[:-1]):
        rho = np.array(rho)
        width_of_rho = np.max(rho[:, 0]) - temps_sorted[idr]
        incre_of_tem = temps_sorted[idr + 1] - temps_sorted[idr]

        width_and_incre.append([width_of_rho / incre_of_tem])

    max_ratio = np.max(width_and_incre)
    if max_ratio > 1:
        suppression = 0.9 / max_ratio
    else:
        suppression = 1

    try:
        p_opt, p_cov = curve_fit(
            fitting_function, temps_sorted, average_deltas_sorted, p0=p, maxfev=1000000
        )
    except:
        print("Curve fit failed")
    x_fit = np.linspace(np.min(temps_sorted) * 0.7, p_opt[-1] - 0.0001, 1000)
    y_fit = fitting_function(x_fit, *p_opt)
    if ax:
        max_rho = 0
        for T, rho in zip(temps_sorted, rhos_sorted):
            rho = np.array(rho)
            ax.axvline(np.min(rho[:, 0]), color="k", linestyle="-", linewidth=1.5)
            ax.plot(
                T + suppression * (rho[:, 0] - T),
                rho[:, 1],
                color="black",
                linewidth=1.5,
            )
            max_rho = np.max([np.max(rho[:, 1]), max_rho])

        ax.scatter(temps_sorted, average_deltas_sorted, c="r", s=70)
        ax.set_xlabel("$T$ [K]", fontsize=20)
        ax.set_ylabel("$\Delta_{nk}$ [meV]", fontsize=20)
        ax.plot(
            x_fit,
            y_fit,
            color="red",
            linestyle="--",
            linewidth=1.5,
        )

        ax.set_xlim([np.min(temps_sorted) * 0.8, np.round(p_opt[-1] * 1.2, decimals=0)])
        ax.set_ylim([0, max_rho])
        ax.set_xticks(
            [
                np.round(np.min(temps_sorted) * 0.8, decimals=0),
                np.round(p_opt[-1] * 1.2, decimals=0),
            ],
            [
                np.round(np.min(temps_sorted) * 0.8, decimals=0),
                np.round(p_opt[-1] * 1.2, decimals=0),
            ],
            fontsize=20,
        )

        ax.set_yticks(
            [0.0, np.round(p_opt[1] * 1.3, decimals=0)],
            [0.0, np.round(p_opt[1] * 1.3, decimals=0)],
            fontsize=20,
        )
    return {
        "temps": temps_sorted,
        "average_deltas": average_deltas_sorted,
        "Tc": p_opt[2],
        "delta0": p_opt[1],
        "expo": p_opt[0],
    }


@calcfunction
def parse_gap_functions(
    retrieved: FolderData,
    prefix: Str = "aiida",
    verbose: Bool = False,
    exclude_points: List = [],
    remove_temps: List = [0, 0],
):
    from io import StringIO

    import numpy as np
    from scipy.optimize import curve_fit

    def fitting_function(T, p, delta_zero, Tc):
        return delta_zero * (1 - (T / Tc) ** p) ** 0.5

    def find_average(data, T):
        data = data[data[:, 1] >= 0]

        T = float(T)

        midpoint = np.average(data[:, 1], weights=data[:, 0] - T)
        return midpoint

    gap_function_arraydata = ArrayData()

    rhos = []
    temps = []
    average_deltas = []
    filenames = [
        f
        for f in retrieved.list_object_names()
        if f.startswith(f"{prefix.value}.imag_aniso_gap0_")
    ]
    if verbose:
        print(filenames)
    for filename in filenames:
        if verbose:
            print(f"Reading {filename}")
        text = retrieved.base.repository.get_object_content(filename)

        parse = np.loadtxt(StringIO(text))
        try:
            temp = parse[:, 0]

            if len(temp) <= 2:
                continue

            temps.append(min(temp))
            rhos.append(parse)

        except IndexError:
            continue

    ntemps = len(temps)
    if ntemps <= 2:
        raise ValueError("less than 2 temperature, can't be fit")

    if verbose:
        print(f"{ntemps} temps: {temps}")
        # print(f"We will exclude points: {exclude_points}")

    sorted_temps, sorted_rhos = zip(*sorted(zip(temps, rhos)))

    if exclude_points != []:
        sorted_temps = [
            sorted_temps[i] for i in range(ntemps) if i not in exclude_points
        ]
        sorted_rhos = [sorted_rhos[i] for i in range(ntemps) if i not in exclude_points]

    sorted_temps = sorted_temps[remove_temps[0] : ntemps - remove_temps[1]]
    sorted_rhos = sorted_rhos[remove_temps[0] : ntemps - remove_temps[1]]

    for temp, rhos in zip(sorted_temps, sorted_rhos):
        gap_function_arraydata.set_array(f"{temp:.2f}".replace(".", "_"), rhos)

    return gap_function_arraydata


def get_seekpath_info(structure):
    seekpath_parameters = get_explicit_kpoints_path(structure)

    seekpath_info = {
        "point_coords": seekpath_parameters["parameters"]["point_coords"],
        "path": seekpath_parameters["parameters"]["path"],
        "explicit_kpoints_linearcoord": seekpath_parameters["parameters"][
            "explicit_kpoints_linearcoord"
        ],
        "explicit_segments": seekpath_parameters["parameters"]["explicit_segments"],
    }
    return seekpath_info


def get_path_labels(seekpath_info):
    path = seekpath_info.get("path")
    plain_path = [path[0][0]]
    explicit_segments = seekpath_info.get("explicit_segments")
    kpoints_indicies = [0]

    for (
        [path_start, path_end],
        [dec_path_start, dec_path_end],
        [seg_start, seg_end],
        [dec_seg_start, dec_seg_end],
    ) in zip(path[:-1], path[1:], explicit_segments[:-1], explicit_segments[1:]):
        if path_end == dec_path_start:
            plain_path.append(dec_path_start)
            kpoints_indicies.append(dec_seg_start)
        else:
            plain_path.extend([path_end, dec_path_start])
            kpoints_indicies.extend([seg_end - 1, dec_seg_start])

    plain_path.append(path[-1][1])
    kpoints_indicies.append(explicit_segments[-1][1] - 1)

    return plain_path, kpoints_indicies


def get_path_labels_from_kpoints(kpoints, seekpath_info, eps=1e-5):
    import numpy as np

    plain_path = []
    point_coords = seekpath_info.get("point_coords")
    kpoints_indicies = []
    for label_number, kpoint in enumerate(kpoints):
        for label, point_coord in point_coords.items():
            if np.linalg.norm(np.array(kpoint) - np.array(point_coord)) < eps:
                plain_path.append(label)
                kpoints_indicies.append(label_number)
                break
    return plain_path, kpoints_indicies


@calcfunction
def update_attributes(bands_data: BandsData, additional_attributes: Dict) -> BandsData:
    """
    A calcfunction that takes a BandsData node and a Dict node,
    and returns a *new* BandsData node with the new attributes updated from dict.

    :param bands_data: The original BandsData node.
    :param additional_attributes: A list of tuples containing the label numbers and labels.
    :return: A new BandsData node with the updated attributes.
    """
    # 1. Clone the original BandsData node
    new_bands = bands_data.clone()

    # 2. Update the labels attribute
    new_bands.base.attributes.set_many(additional_attributes.get_dict())

    return new_bands


def check_stability_matdyn_base(
    workchain: WorkChainNode,
    tolerance: float = -8.065,  # cm^{-1}
) -> tuple[bool, str]:
    """Check if the matdyn.x interpolated phonon band structure is stable."""
    THZ_TO_CM = 33.356
    bands = workchain.outputs.output_phonon_bands.get_bands() * THZ_TO_CM  # unit: THz
    min_freq = numpy.min(bands)
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


from collections import defaultdict


def aggregate_recursive(source, target):
    """
    Recursively traverse the source dictionary and aggregate the "leaf" values to the list in the target dictionary.
    """
    for key, value in source.items():
        # Case 1: If the value is a dictionary, we need to continue深入
        if isinstance(value, dict):
            # In the target, get or create a new dictionary as the next layer
            # setdefault will return the value corresponding to the key:
            # - If the key exists, return target[key]
            # - If the key does not exist, set target[key] = {} and return {}
            target_node = target.setdefault(key, {})

            # Recursively call, enter the next layer
            aggregate_recursive(value, target_node)

        # Case 2: If the value is not a dictionary (numbers, strings, lists, etc.), this is the "leaf" we want to aggregate
        else:
            # In the target, get or create a list
            target_list = target.setdefault(key, [])

            # Append the value to the list
            target_list.append(value)

    return target


def find_finest_qdensity(phonons):
    pattern = re.compile(r"matdyn_(03|05|07)_")
    new_phonons = {}

    for key in [
        "pw_uuid",
        "ph_uuid",
        "kgrid_dfpt",
        "fermi_energy_coarse",
        "total_energy",
        "ecut",
        "scf_smearing",
        "matdyn_highest_phonon_frequency",
        "matdyn_uuid",
        "matdyn_retrieved_uuid",
        "phonon_bands_uuid",
        "qpoint_density",
        "qgrid_dfpt",
    ]:
        if key in phonons:
            new_phonons[key] = phonons[key]

    found_qdensities = set()
    for key in phonons.keys():
        match = pattern.search(key)
        if match:
            found_qdensities.add(match.group(1))

    if found_qdensities:
        min_qdensity = min(found_qdensities)

        new_phonons["qpoint_density"] = float(int(min_qdensity) / 10)
        new_phonons["ph_uuid"] = phonons[f"ph_{min_qdensity}_uuid"]
        new_phonons["qgrid_dfpt"] = phonons[f"qgrid_dfpt_{min_qdensity}"]
        new_phonons["matdyn_uuid"] = phonons[f"matdyn_{min_qdensity}_uuid"]
        new_phonons["matdyn_retrieved_uuid"] = phonons[
            f"matdyn_{min_qdensity}_retrieved_uuid"
        ]
        new_phonons["phonon_bands_uuid"] = phonons[
            f"matdyn_{min_qdensity}_phonon_bands_uuid"
        ]

    return new_phonons


def check_base_json(details, log=print):
    statistics = {
        "phonons": {
            "matdyn_highest_phonon_frequency": [],
            "pw_uuid": [],
            "kgrid_dfpt": {
                "mesh": [],
                "uuid": [],
            },
            "matdyn_uuid": [],
            "matdyn_retrieved_uuid": [],
            "qpoint_density": [],
            "qgrid_dfpt": {
                "mesh": [],
                "uuid": [],
            },
            "ph_uuid": [],
            "phonon_bands_uuid": [],
        },
        "supercon": {
            "a2f_uuid": [],
            "allen_dynes_tc": [],
            "aniso_gap_function_uuid": [],
            "aniso_info": {
                "Tc": [],
                "average_deltas": [],
                "delta0": [],
                "expo": [],
                "temps": [],
            },
            "cell_volume": [],
            "ecut": [],
            "epw_el_band_structure_uuid": [],
            "epw_ph_band_structure_uuid": [],
            "epw_uuid": [],
            "fermi_energy_coarse": [],
            "fermi_window": [],
            "highest_phonon_frequency": [],
            "iso_tc": [],
            "kgrid_dfpt": {
                "mesh": [],
                "uuid": [],
            },
            "kgrid_epw_coarse": {
                "mesh": [],
                "uuid": [],
            },
            "kgrid_epw_fine": {
                "mesh": [],
                "uuid": [],
            },
            "qgrid_epw_coarse": {
                "mesh": [],
                "uuid": [],
            },
            "qgrid_epw_fine": {
                "mesh": [],
                "uuid": [],
            },
            "lambda": [],
            "number_of_wannier_functions": [],
            "omega_log": [],
            "pw_uuid": [],
            "qe_el_band_structure_uuid": [],
            "scf_smearing": [],
            "smearing_q": [],
            "space_group_number": [],
            "structure_uuid": [],
            "total_energy": [],
            "type": [],
        },
    }

    for detail in details.values():
        aggregate_recursive(detail, statistics)

    for k, v in statistics["supercon"].items():
        if isinstance(v, dict):
            log(f"{k:40s}:")
            for kk, vv in v.items():
                log(f"  {kk:38s}: {len(vv):5d}")
        else:
            log(f"{k:40s}: {len(v):5d}")
    for k, v in statistics["phonons"].items():
        if isinstance(v, dict):
            log(f"{k:40s}:")
            for kk, vv in v.items():
                log(f"  {kk:38s}: {len(vv):5d}")
        else:
            log(f"{k:40s}: {len(v):5d}")


def load_scon(
    profile,
    label,
    log=print,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

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

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue

            details_entry = {mc3d_id: {"supercon": {}}}
            details_entry[mc3d_id]["supercon"]["structure_uuid"] = structure.uuid
            details_entry[mc3d_id]["supercon"]["cell_volume"] = (
                structure.get_cell_volume()
            )

            ase_atoms = structure.get_ase()
            symmetry = check_symmetry(ase_atoms, symprec=1e-6)
            details_entry[mc3d_id]["supercon"]["space_group_number"] = symmetry.number

            try:
                inputs_parameters = (
                    workchain_node.inputs.epw_final.parameters.get_dict()
                )
                details_entry[mc3d_id]["supercon"]["number_of_wannier_functions"] = (
                    inputs_parameters.get("INPUTEPW", {}).get("nbndsub")
                )
                # details_entry[mc3d_id]["supercon"]["smearing_q"] = (
                #     inputs_parameters.get("INPUTEPW", {}).get("degaussq")
                # )
                details_entry[mc3d_id]["supercon"]["fermi_window"] = (
                    inputs_parameters.get("INPUTEPW", {}).get("fsthick")
                )
                details_entry[mc3d_id]["supercon"]["type"] = "FSR"
            except Exception as e:
                log(f"SKIPPING: parameters not found in {workchain_node.uuid} {extras}")
                count_skipped += 1
            try:
                epw_final = (
                    workchain_node.base.links.get_outgoing(
                        link_label_filter="epw_final"
                    )
                    .first()
                    .node
                )
                details_entry[mc3d_id]["supercon"]["epw_final_uuid"] = (
                    epw_final.uuid
                )

                input_string = epw_final.base.repository.get_object_content('aiida.in')
                
                degaussq = float(
                    re.search(
                        r'^\s*degaussq\s*=\s*([+-]?\d*\.?\d+(?:[dDeE][+-]?\d+)?)',
                        input_string,
                        re.MULTILINE
                    ).group(1).replace('d', 'e').replace('D', 'E')
                )
                degaussw = float(
                    re.search(
                        r'^\s*degaussw\s*=\s*([+-]?\d*\.?\d+(?:[dDeE][+-]?\d+)?)',
                        input_string,
                        re.MULTILINE
                    ).group(1).replace('d', 'e').replace('D', 'E')
                )
                
                details_entry[mc3d_id]["supercon"]["smearing_q"] = degaussq
                details_entry[mc3d_id]["supercon"]["smearing_w"] = degaussw
                details_entry[mc3d_id]["supercon"]['kgrid_epw_fine'] = {}
                details_entry[mc3d_id]["supercon"]['qgrid_epw_fine'] = {}

                details_entry[mc3d_id]["supercon"]['kgrid_epw_fine']["mesh"] = (
                    epw_final.inputs.kfpoints.get_kpoints_mesh()[0]
                )
                details_entry[mc3d_id]["supercon"]['qgrid_epw_fine']["mesh"] = (
                    epw_final.inputs.qfpoints.get_kpoints_mesh()[0]
                )
                details_entry[mc3d_id]["supercon"]['kgrid_epw_fine']["uuid"] = (
                    epw_final.inputs.kfpoints.uuid
                )
                details_entry[mc3d_id]["supercon"]['qgrid_epw_fine']["uuid"] = (
                    epw_final.inputs.qfpoints.uuid
                )
            except Exception as e:
                log(f"SKIPPING: parameters not found in {workchain_node.uuid} {extras}")
                count_skipped += 1

            wlog, _lambda, Tc = calculate_Allen_Dynes_tc(a2f)
            iso_tc = calculate_iso_tc(max_eigenvalue)

            details_entry[mc3d_id]["supercon"]["iso_tc"] = iso_tc

            details_entry[mc3d_id]["supercon"]["omega_log"] = wlog
            details_entry[mc3d_id]["supercon"]["lambda"] = _lambda
            details_entry[mc3d_id]["supercon"]["allen_dynes_tc"] = Tc
            details_entry[mc3d_id]["supercon"]["a2f_uuid"] = a2f.uuid

            details = update_mapping(details, details_entry)

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def load_epw(
    profile,
    label,
    log=print,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    qb_epw = (
        orm.QueryBuilder()
        .append(
            orm.Group,
            filters={"label": label},
            tag="epw_group",
        )
        .append(
            orm.WorkChainNode,
            project=["*"],
            tag="epw_wc",
            with_group="epw_group",
        )
    )

    for workchain_node in tqdm(qb_epw.all(flat=True), total=qb_epw.count()):
        try:
            extras = workchain_node.base.extras.all

            if "source_db" not in workchain_node.base.extras.all:
                extras = workchain_node.inputs.structure.base.extras.all
            else:
                extras = workchain_node.base.extras.all

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if mc3d_id not in details:
                continue
            details_entry = {mc3d_id: {"supercon": {}}}

            pw = (
                workchain_node.base.links.get_outgoing(link_label_filter="w90_bands")
                .first()
                .node.base.links.get_outgoing(link_label_filter="scf")
                .first()
                .node
            )
            
            details_entry[mc3d_id]["supercon"]['kgrid_dfpt'] = {}
            details_entry[mc3d_id]["supercon"]['kgrid_dfpt']["mesh"] = pw.inputs.kpoints.get_kpoints_mesh()[0]
            details_entry[mc3d_id]["supercon"]['kgrid_dfpt']["uuid"] = pw.inputs.kpoints.uuid
            details_entry[mc3d_id]["supercon"]["pw_uuid"] = pw.uuid
            details_entry[mc3d_id]["supercon"]["fermi_energy_coarse"] = (
                pw.outputs.output_parameters.get("fermi_energy")
            )
            details_entry[mc3d_id]["supercon"]["total_energy"] = (
                pw.outputs.output_parameters.get("energy")
            )
            details_entry[mc3d_id]["supercon"]["ecut"] = (
                pw.outputs.output_parameters.get("wfc_cutoff")
            )
            details_entry[mc3d_id]["supercon"]["scf_smearing"] = (
                pw.outputs.output_parameters.get("degauss")
            )

            epw = (
                workchain_node.base.links.get_outgoing(link_label_filter="epw")
                .first()
                .node
            )
            kpoints = epw.inputs.kpoints
            qpoints = epw.inputs.qpoints

            details_entry[mc3d_id]["supercon"]['kgrid_epw_coarse'] = {}
            details_entry[mc3d_id]["supercon"]['qgrid_epw_coarse'] = {}
            details_entry[mc3d_id]["supercon"]['kgrid_epw_coarse']["mesh"] = (
                kpoints.get_kpoints_mesh()[0]
            )
            details_entry[mc3d_id]["supercon"]['qgrid_epw_coarse']["mesh"] = (
                qpoints.get_kpoints_mesh()[0]
            )
            details_entry[mc3d_id]["supercon"]['kgrid_epw_coarse']["uuid"] = kpoints.uuid
            details_entry[mc3d_id]["supercon"]['qgrid_epw_coarse']["uuid"] = qpoints.uuid

            details_entry[mc3d_id]["supercon"]["epw_uuid"] = epw.uuid

            details = update_mapping(details, details_entry)

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def load_aniso(
    profile,
    label,
    log=print,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    qb_aniso = (
        orm.QueryBuilder()
        .append(orm.Group, filters={"label": label}, tag="aniso_group")
        .append(
            orm.ArrayData,
            project=["*"],
            tag="aniso_calc",
            with_group="aniso_group",
        )
    )
    for arraydata_node in tqdm(qb_aniso.all(flat=True), total=qb_aniso.count()):
        try:
            extras = arraydata_node.base.extras.all

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue

            details_entry = {mc3d_id: {"supercon": {}}}
            details_entry[mc3d_id]["supercon"]["aniso_gap_function_uuid"] = (
                arraydata_node.uuid
            )

            result = plot_gap_function_arraydata(
                arraydata_node,
                p_opt=arraydata_node.base.extras.get("suggested_p", None),
            )

            details_entry[mc3d_id]["supercon"]["aniso_info"] = result
            try:
                epw_aniso = arraydata_node.creator.inputs.retrieved.creator
                details_entry[mc3d_id]["supercon"]["epw_aniso_uuid"] = epw_aniso.uuid
            except Exception as e:
                log(f"SKIPPING: cannot find epw_aniso from {arraydata_node.uuid}")
                count_skipped += 1
                continue
            details = update_mapping(details, details_entry)

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def load_scf_from_elph(
    profile,
    label,
    qdensity,
    log=print,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    qb_elph = (
        orm.QueryBuilder()
        .append(
            orm.Group,
            filters={"label": label},
            tag="elph",
        )
        .append(
            orm.WorkChainNode,
            project=["*"],
            tag="elph_wc",
            with_group="elph",
            filters={"attributes.exit_status": 0},
        )
        .append(
            orm.WorkChainNode,
            project=["*"],
            with_incoming="elph_wc",
            edge_filters={"label": "scf"},
            tag="scf_wc",
        ).append(
            orm.WorkChainNode,
            project=["*"],
            with_incoming="elph_wc",
            edge_filters={"label": "ph_base"},
            tag="ph_base_wc",
        )
    )
    for workchain_node, pw_workchain_node, ph_base_workchain_node in tqdm(qb_elph.all(), total=qb_elph.count()):
        try:
            extras = workchain_node.base.extras.all

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue
            if mc3d_id not in details:
                continue

            details_entry = {mc3d_id: {"phonons": {}}}
            details_entry[mc3d_id]["phonons"]["pw_workchain_uuid"] = (
                pw_workchain_node.uuid
            )

            details_entry[mc3d_id]["phonons"]["pw_uuid"] = pw_workchain_node.uuid
            
            details_entry[mc3d_id]["phonons"]['kgrid_dfpt'] = {}
            details_entry[mc3d_id]["phonons"]['kgrid_dfpt']["mesh"] = pw_workchain_node.inputs.kpoints.get_kpoints_mesh()[0]
            details_entry[mc3d_id]["phonons"]['kgrid_dfpt']["uuid"] = pw_workchain_node.inputs.kpoints.uuid
            details_entry[mc3d_id]["phonons"]["fermi_energy_coarse"] = (
                pw_workchain_node.outputs.output_parameters.get("fermi_energy")
            )
            details_entry[mc3d_id]["phonons"]["total_energy"] = (
                pw_workchain_node.outputs.output_parameters.get("energy")
            )
            details_entry[mc3d_id]["phonons"]["ecut"] = (
                pw_workchain_node.outputs.output_parameters.get("wfc_cutoff")
            )
            details_entry[mc3d_id]["phonons"]["scf_smearing"] = (
                pw_workchain_node.outputs.output_parameters.get("degauss")
            )

            details_entry[mc3d_id]["phonons"][f"ph_{qdensity}_uuid"] = ph_base_workchain_node.uuid

            details_entry[mc3d_id]["phonons"][f'qgrid_dfpt_{qdensity}'] = {}
            details_entry[mc3d_id]["phonons"][f'qgrid_dfpt_{qdensity}']["mesh"] = ph_base_workchain_node.inputs.ph.qpoints.get_kpoints_mesh()[0]
            details_entry[mc3d_id]["phonons"][f'qgrid_dfpt_{qdensity}']["uuid"] = ph_base_workchain_node.inputs.ph.qpoints.uuid

            details = update_mapping(details, details_entry)

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def load_matdyn_from_elph(
    profile,
    label,
    qdensity,
    log=print,
    details={},
    check_stability=True,
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    qb_matdyn = (
        orm.QueryBuilder()
        .append(
            orm.Group,
            filters={"label": label},
            tag="matdyn",
        )
        .append(
            orm.WorkChainNode,
            project=["*"],
            tag="matdyn_wc",
            with_group="matdyn",
            filters={"attributes.exit_status": 0},
        )
        .append(
            orm.FolderData,
            project=["*"],
            with_incoming="matdyn_wc",
            edge_filters={"label": "retrieved"},
        )
    )

    for workchain_node, retrieved_matdyn in tqdm(
        qb_matdyn.all(), total=qb_matdyn.count()
    ):
        try:
            extras = workchain_node.base.extras.all

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue

            if check_stability and details.get(mc3d_id, {}).get("supercon", {}) == {}:
                is_stable, _ = check_stability_matdyn_base(workchain_node)
                if not is_stable:
                    log(f"SKIPPING: {mc3d_id} is not stable")
                    count_skipped += 1
                    continue

            details_entry = {mc3d_id: {"phonons": {}}}
            details_entry[mc3d_id]["phonons"][f"matdyn_{qdensity}_uuid"] = (
                workchain_node.uuid
            )
            details_entry[mc3d_id]["phonons"][f"matdyn_{qdensity}_retrieved_uuid"] = (
                retrieved_matdyn.uuid
            )
            details_entry[mc3d_id]["phonons"][
                f"matdyn_{qdensity}_phonon_bands_uuid"
            ] = workchain_node.outputs.output_phonon_bands.uuid
            # unit of phonon bands is THz
            details_entry[mc3d_id]["phonons"]["matdyn_highest_phonon_frequency"] = (
                workchain_node.outputs.output_phonon_bands.get_array("bands").max()
                * THZ_TO_MEV
            )

            details = update_mapping(details, details_entry)

            count_successful += 1

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def load_qe_el_banddata(
    profile,
    label,
    log=print,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    qb_bands = (
        orm.QueryBuilder()
        .append(orm.Group, filters={"label": label}, tag="bands_qe")
        .append(
            orm.BandsData,
            project=["*"],
            with_group="bands_qe",
        )
    )

    for bands_data in tqdm(qb_bands.all(flat=True), total=qb_bands.count()):
        try:
            extras = bands_data.base.extras.all

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue

            if mc3d_id not in details:
                continue

            details_entry = {mc3d_id: {"supercon": {}}}

            details_entry[mc3d_id]["supercon"]["qe_el_band_structure_uuid"] = (
                bands_data.uuid
            )

            details = update_mapping(details, details_entry)

        except Exception as exception:
            log(f"Found exception for {bands_data.pk} with {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue


def load_epw_int_banddata(
    profile,
    label,
    log=print,
    details={},
):
    count_successful = 0
    count_skipped = 0

    from aiida import load_profile, orm

    load_profile(profile, allow_switch=True)

    qb_bands = (
        orm.QueryBuilder()
        .append(orm.Group, filters={"label": label}, tag="bands_int")
        .append(
            orm.BandsData,
            project=["*"],
            tag="bands",
            with_group="bands_int",
        )
    )

    for bands_data in tqdm(qb_bands.all(flat=True), total=qb_bands.count()):
        try:
            extras = bands_data.base.extras.all

            if "source_id" not in extras:
                log(f"SKIPPING: source_id not found in {bands_data.pk}  {extras}")
                count_skipped += 1
                continue

            mc3d_id = get_mc3d_id_from_extras(extras)

            if not mc3d_id:
                log(f"SKIPPING: MC3D ID not assigned to {extras}")
                count_skipped += 1
                continue

            if mc3d_id not in details:
                continue

            details_entry = {mc3d_id: {"supercon": {}}}
            band_type = extras["band_type"]
            if band_type == "el_band_structure":
                details_entry[mc3d_id]["supercon"]["epw_el_band_structure_uuid"] = (
                    bands_data.uuid
                )
            elif band_type == "ph_band_structure":
                details_entry[mc3d_id]["supercon"]["epw_ph_band_structure_uuid"] = (
                    bands_data.uuid
                )

                highest_phonon_frequency = numpy.max(bands_data.get_bands())
                details_entry[mc3d_id]["supercon"]["highest_phonon_frequency"] = (
                    highest_phonon_frequency
                )
            else:
                log(f"SKIPPING: band_type not found in {extras}")
                count_skipped += 1
                continue

            details = update_mapping(details, details_entry)

        except Exception as exception:
            log(f"Found exception for {extras}: {exception}")
            traceback.print_exc()
            count_skipped += 1
            continue
