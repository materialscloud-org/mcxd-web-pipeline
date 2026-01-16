# The `mc3d/pbesol-v1/supercon` Dataset Generation Script

This code `scripts/gen.py` is used to extract the results from supercond database and generate the `base.json` file for the deploy on MC3D discover webpage.

### 📋 **Prerequisites**

Before running the script, you will need two things:

1. **AiiDA Environment**: This script requires a working AiiDA environment (e.g., with `aiida-core` installed).

2. **Data Archives**: You must download two required archive files from the [Material Cloud Archive](https://doi.org/10.24435/materialscloud:n9-a7).

## 🚀 Usage

The scripts/gen.py script offers two methods for loading the data, depending on your setup.

### **Option 1: Using an AiiDA Profile**

If you have already imported the .aiida archives into an AiiDA profile, you can specify the profile name directly:

```bash
python scripts/gen.py --profile "YOUR_PROFILE_NAME"
```

### **Option 2: Loading from Local Archive Files**

If you have the two .aiida files (`QE-screening.aiida` and `EPW-screening.aiida`) saved in a local directory, you can provide the path to that directory. The script will find and load them using `SqliteZipBackend`.

```bash
python scripts/gen.py --archive "/path/to/your/archives"
```

## 💾 Output

Upon successful execution, the script will generate a `base.json` file in the working directory. This file contains all the detailed calculation data extracted from the archives.

The base.json file has the following structure for each material:

```json
{
    "mc3d-id": {
        "phonons": {
            "matdyn_retrieved_uuid"             : the retrieved folder for |q|=0.7 A^{-1},
            "matdyn_uuid"                       : the uuid that points to the MatdynBaseWorkChain for |q|=0.7 A^{-1},
            "matdyn_highest_phonon_frequency"   : the highest frequency (in meV) from the matdyn with highest available |q|,
            "pw_uuid"                           : the uuid that points to the PwBaseWorkChain,
            "ph_uuid"                           : the uuid that points to the PwBaseWorkChain,
            "kgrid_dfpt" : {
                "mesh"                          : the kpoint mesh for the SCF process in DFPT calculation,
                "uuid"                          : the uuid to the KpointsData of kpoints for the SCF process in DFPT calculation,
            },
            "qgrid_dfpt" : {
                "mesh"                          : the qpoint mesh for the DFPT calculation,
                "uuid"                          : the uuid to the KpointsData of qpoints for the DFPT calculation,
            },
            "phonon_bands_uuid"                 : the uuid to the phonon dispersion from MatdynBaseWorkChain,
            "qpoint_density"                    : the density of qpoints in the DFPT calculation (A^{-1}),
            "scf_smearing"                      : the smearing used for the SCF process,
            "total_energy"                      : the total energy from the SCF calculation.
        },
        "supercon": {
            "a2f_uuid"                    : the uuid of the a2f ArrayData,
            "allen_dynes_tc"              : transition temperature evaluated by Allen-Dynes formula,
            "aniso_gap_function_uuid"     : the uuid of the anisotropic gap function ArrayData,
            "aniso_info": {
                "Tc"                      : transition temperature evaluated by anisotropic Migdal-Eliashberg theory,
                "average_deltas"          : the average of the gap function,
                "delta0"                  : the anisotropic gap at 0K,
                "expo"                    : the exponent of fitted from the gap function,
                "temps"                   : the anisotropic transition temperatures of the gap function,
            },
            "epw_el_band_structure_uuid"  : the uuid of the epw el band structure,
            "epw_ph_band_structure_uuid"  : the uuid of the epw ph band structure,
            "epw_uuid"                    : the uuid of the epw workchain,
            "fermi_energy_coarse"         : the fermi energy of the coarse grid,
            "fermi_window"                : the fermi window,
            "highest_phonon_frequency"    : the highest phonon frequency from EPW interpolated phonon bands,
            "iso_tc"                      : the isotropic transition temperature,
            "kgrid_dfpt": {
                "mesh"                    : the kpoint mesh in SCF calculation,
                "uuid"                    : the uuid to the KpointsData of kpoint in SCF calculation
            },
            "kgrid_epw_coarse": {
                "mesh"                    : the kpoint mesh in NSCF calculation, subsequently used in EPW interpolation,
                "uuid"                    : the uuid to the KpointsData of kpoint in NSCF calculation,
            },
            "kgrid_epw_fine": {
                "mesh"                    : the fine kpoint mesh for the EPW interpolation,
                "uuid"                    : the uuid to the KpointsData of fine kpoint mesh for the EPW interpolation,
            },
            "lambda"                      : the electron-phonon coupling strength,
            "number_of_wannier_functions" : the number of wannier functions,
            "omega_log"                   : the log average of phonon frequency (in meV),
            "pw_uuid"                     : the uuid of the scf workchain,
            "qe_el_band_structure_uuid"   : the uuid of the qe electron band structure,
            "qgrid_epw_coarse": {
                "mesh"                    : the coarse qpoint mesh in DFPT calculation,
                "uuid"                    : the uuid to the KpointsData of qpoint in DFPT calculation,
            },
            "qgrid_epw_fine": {
                "mesh"                    : the fine qpoint mesh for the EPW interpolation,
                "uuid"                    : the uuid to the KpointsData of fine qpoint mesh for the EPW interpolation,
            },
            "scf_smearing"                : the smearing in the scf calculation in Wannier90 workchain,
            "smearing_q"                  : the smearing of phonon in EPW interpolation,
            "space_group_number"          : the space group number of the structure,
            "structure_uuid"              : the uuid to the StructureData,
            "total_energy"                : the total energy in the scf calculation in Wannier90 workchain,
            "type"                        : whether the calculation is in full-bandwidth or Fermi-surface restricted,
        }
    }
}
```

## Organization of the MC3D discover website:

### **meta info**

The `meta.json` contains list of property columns for the MC3D landing page.

**Phonons section (QE, SSSP)**

We have 3 levels of qpoints_density, I have selected the successful MatdynBaseWorkChains with stable phonons (>5cm$^{-1}$) from the paper/workchains/phbands-qe/{qpoints_density}/matdyn groups:

- |q| = 0.3, here there are 198 stable phonons,
- |q| = 0.5, here there are 587 stable phonons,
- |q| = 0.7, here there are 2715 stable phonons,

For the interactive phonon visualization pipeline (`phonon-web-tools` in https://github.com/materialscloud-org/interactive-phonon-visualizer), the required data is in the following AiiDA nodes:

- QE `scf.in` and `scf.out` - get from `pw_uuid`,
- QE `matdyn.modes` file - get from `matdyn_{qdensity}_retrieved_uuid`
- High-symmetry Q-points - this should not be auto-generated by seekpath, but rather taken from the associated phonons band node (`matdyn_retrieved_node.creator.outputs.output_phonon_bands.labels`).

**Superconductivity section (PseudoDojo)**

_Electronic band structures_

- uuid to QE el band structure [key: qe_el_band_structure_uuid, type: BandsData] (PseudoDojo)
- uuid to EPW interpolated electron band structure [key: epw_el_band_structure_uuid, type: BandsData]

_Static phonon dispersion and spectral function_

- uuid to EPW interpolated phonon band structure [key: epw_ph_band_structure_uuid, type: BandsData] (PseudoDojo)
- uuid to spectral function [key: a2f_uuid, type: ArrayData]

_Anisotropic gap function_

- uuid to anisotropic gap functions [key: aniso_gap_function_uuid, type: orm.ArrayData] and their fitting
