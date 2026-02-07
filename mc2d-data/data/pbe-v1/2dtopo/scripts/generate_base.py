import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

original_data_json = os.path.join(SCRIPT_DIR, "../original_data/2dtopo_data.json")
hwcc_dir = os.path.join(SCRIPT_DIR, "../hwcc")
output_path = os.path.join(SCRIPT_DIR, "../base.json")

with open(original_data_json, "r") as f:
    data = json.load(f)

# Mapping of {Formula: {"id": mc2d_id, "file": filename_no_ext}}
formula_to_id_mapping = {
    "Pt2HgSe3": {"id": "mc2d-400", "file": "Hg2Pt4Se6", "citation": "Marrazzo2019"},
    "WTe2": {"id": "mc2d-255", "file": "Te4W2", "citation": "Marrazzo2019"},
    "RhTaTe4": {"id": "mc2d-488", "file": "Rh2Ta2Te8", "citation": "Marrazzo2019"},
    "AsCuLi2": {"id": "mc2d-1288", "file": "AsCuLi2", "citation": "Marrazzo2019"},
    "MoTe2": {"id": "mc2d-206", "file": "Mo2Te4", "citation": "Marrazzo2019"},
    "TiCu2Te3": {"id": "mc2d-864", "file": "Cu4Te6Ti2", "citation": "Marrazzo2019"},
    "IrNbTe4": {"id": "mc2d-396", "file": "Ir2Nb2Te8", "citation": "Marrazzo2019"},
    "ZrBr": {"id": "mc2d-70", "file": "Br2Zr2", "citation": "Marrazzo2019"},
    "Bi": {"id": "mc2d-18", "file": "Bi2", "citation": "Marrazzo2019"},
    "TiNI": {"id": "mc2d-192", "file": "I2N2Ti2", "citation": "Marrazzo2019"},
    "In2ZnS4": {"id": "mc2d-567", "file": "In2S4Zn", "citation": "Marrazzo2019"},
    "TaIrTe4": {"id": "mc2d-706", "file": "Ir2Ta2Te8", "citation": "Marrazzo2019"},
    "ZrCl": {"id": "mc2d-126", "file": "Cl2Zr2", "citation": "Marrazzo2019"},
    "Fe4O6": {"id": "mc2d-2337", "file": "Fe4O6", "citation": "Grassano2023"},
    "Mo2O17Ta2": {"id": "mc2d-2315", "file": "Mo2O17Ta2", "citation": "Grassano2023"},
    "C2H6Fe2O8P2": {
        "id": "mc2d-1956",
        "file": "C2H6Fe2O8P2",
        "citation": "Grassano2023",
    },
    "Br6V2": {"id": "mc2d-2312", "file": "Br6V2", "citation": "Grassano2023"},
    "Hf2Te10": {"id": "mc2d-1775", "file": "Hf2Te10", "citation": "Grassano2023"},
    "Hg4N4S4": {"id": "mc2d-2366", "file": "Hg4N4S4", "citation": "Grassano2023"},
    "Te10Zr2": {"id": "mc2d-2514", "file": "Te10Zr2", "citation": "Grassano2023"},
    "Cl2Hf2": {"id": "mc2d-2474", "file": "Cl2Hf2", "citation": "Grassano2023"},
    "Br2Hf2": {"id": "mc2d-2291", "file": "Br2Hf2", "citation": "Grassano2023"},
    "I4Mo2S4": {"id": "mc2d-1839", "file": "I4Mo2S4", "citation": "Grassano2023"},
    "BaCr2N2O8": {"id": "mc2d-2352", "file": "BaCr2N2O8", "citation": "Grassano2023"},
}

# rename keys to something reasonable
subkey_rename_map = {
    "band_structure_with_SOC": "soc_bandstructure_uuid",
    "fermi_with_SOC": "fermi_with_SOC",
    "band_structure_without_SOC": "nosoc_bandstructure_uuid",
    "fermi_without_SOC": "fermi_without_SOC",
    "inversion_strength": "inversion_strength",
    "band_gap": "soc_band_gap",
    "structure": "structure_uuid",  # probably wont need, but useful for debugging.
    "phonons": "soc_phonon_uuid",
}

final_output = {}


def round_floats(obj, ndigits=4):
    if isinstance(obj, dict):
        return {k: round_floats(v, ndigits) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [round_floats(x, ndigits) for x in obj]
    elif isinstance(obj, float):
        return round(obj, ndigits)
    else:
        return obj


for formula, mapping_info in formula_to_id_mapping.items():
    mc2d_id = mapping_info["id"]
    filename = mapping_info["file"]

    citations = [mapping_info["citation"]]

    # 1.HWCC files
    hwcc_data = {}
    hwcc_file_path = os.path.join(hwcc_dir, f"{filename}.json")

    try:
        with open(hwcc_file_path, "r") as f:
            hwcc_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: HWCC file not found: {hwcc_file_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON in {hwcc_file_path}")

    if formula in data:
        # Rename keys from original data
        clean_entry = {
            subkey_rename_map[k]: round_floats(data[formula][k])
            for k in subkey_rename_map
            if k in data[formula]
        }

        # 3. Assign to the mapped ID
        final_output[mc2d_id] = clean_entry
        final_output[mc2d_id]["hwcc"] = hwcc_data

        # Add the relevant citation to all of these.
        final_output[mc2d_id]["citations"] = citations

    else:
        print(f"Skipping {formula}: Not found in original data.")

# Add strained band gap values for selected materials
strain_percent = {
    "mc2d-206": 3,  # MoTe2
    "mc2d-255": 2.0,  # WTe2
    "mc2d-70": 1,  # ZrBr
    "mc2d-126": 3,  # ZrCl
}

for mc2d_id, value in strain_percent.items():
    if mc2d_id in final_output:
        final_output[mc2d_id]["strain_percent"] = value


# 4. Save the restructured JSON
with open(output_path, "w") as f:
    json.dump(final_output, f, indent=2)
