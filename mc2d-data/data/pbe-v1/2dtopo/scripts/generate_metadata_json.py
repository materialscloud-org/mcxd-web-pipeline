## Script to generate "from the original malformed data files the intermediate data structure for conversion",
## WARNING - the original data has misassigned *atleast* some source_db ids, other data may also be misassigned.
## Take care if modifying this to not carry through incorrect data.

import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
original_data_json = os.path.join(SCRIPT_DIR, "../original_data/2dtopo_data.json")

with open(original_data_json, "r") as f:
    data = json.load(f)


# only some keys are really needed during the data merger.
keep_keys = [
    "structure",
    "inversion_strength",
    "band_structure_with_SOC",
    "band_structure_without_SOC",
    "band_gap",
    "phonons",
]

filtered_data = {
    material: {k: v for k, v in details.items() if k in keep_keys}
    for material, details in data.items()
}


Pd2HgSe3 = "NO EQUIVALENT MATERIAL ON MC2D ? MAYBE 400 "

formula_to_id_mapping = {
    "Pt2HgSe3": "mc2d-400",
    "WTe2": "mc2d-255",
    "RhTaTe4": "mc2d-488",
    "AsCuLi2": "mc2d-1288",
    "MoTe2": "mc2d-206",
    "TiCu2Te3": "mc2d-864",
    "IrNbTe4": "mc2d-396",
    "ZrBr": "mc2d-70",
    "Bi": "mc2d-18",
    "TiNI": "mc2d-192",
    "In2ZnS4": "mc2d-567",
    "TaIrTe4": "mc2d-706",
    "ZrCl": "mc2d-126",
    "Fe4O6": "mc2d-2337",
    "Mo2O17Ta2": "mc2d-2315",
    "C2H6Fe2O8P2": "mc2d-1956",
    "Br6V2": "mc2d-2312",
    "Hf2Te10": "mc2d-1775",
    "Hg4N4S4": "mc2d-2366",
    "Te10Zr2": "mc2d-2514",
    "Cl2Hf2": "mc2d-2474",
    "Br2Hf2": "mc2d-2291",
    "I4Mo2S4": "mc2d-1839",
    "BaCr2N2O8": "mc2d-2352",
}

remapped_data = {}
for formula, mc2d_id in formula_to_id_mapping.items():
    if formula in filtered_data:
        remapped_data[mc2d_id] = filtered_data[formula]
    else:
        print(f"Warning: {formula} found in mapping but missing from original JSON.")
filtered_data = remapped_data

# rename keys to something reasonable
subkey_rename_map = {
    "band_structure_with_SOC": "soc_bandstructure_uuid",
    "band_structure_without_SOC": "nosoc_bandstructure_uuid",
    "inversion_strength": "inv_strength",
    "band_gap": "band_gap",
    "structure": "structure_uuid",
    "phonons": "soc_phonon_uuid",
}

final_output = {}
for formula, mc2d_id in formula_to_id_mapping.items():
    if formula in data:
        # 1. Rename and Filter subkeys
        clean_entry = {
            subkey_rename_map[k]: data[formula][k]
            for k in subkey_rename_map
            if k in data[formula]
        }

        # 3. Assign to the mapped ID
        final_output[mc2d_id] = clean_entry
    else:
        print(f"Skipping {formula}: Not found in original data.")

# Save the restructured JSON
output_path = os.path.join(SCRIPT_DIR, "../data/base.json")
with open(output_path, "w") as f:
    json.dump(final_output, f, indent=4)
