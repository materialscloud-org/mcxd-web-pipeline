# The `mc3d/pbesol-v1/mechanical` Dataset Generation Script

This code `scripts/gen.py` is used to extract the results from mechanical database and generate the `base.json` file for the deploy on MC3D discover webpage.

### 📋 **Prerequisites**

Before running the script, you will need two things:

1. **AiiDA Environment**: This script requires a working AiiDA environment (e.g., with `aiida-core` installed).

2. **Data Archives**: You must download the required archive files from the [Material Cloud Archive](https://doi.org/10.24435/materialscloud:7a-cx).

## 🚀 Usage

The scripts/gen.py script offers two methods for loading the data, depending on your setup.

### **Option 1: Using an AiiDA Profile**

If you have already imported the .aiida archives into an AiiDA profile, you can specify the profile name directly:

```bash
python scripts/gen.py --profile "YOUR_PROFILE_NAME"
```

### **Option 2: Loading from Local Archive Files**

If you have the .aiida files saved in a local directory, you can provide the path to that directory. The script will find and load them using `SqliteZipBackend`.

```bash
python scripts/gen.py --archive "/path/to/your/archives"
```

## 💾 Output

Upon successful execution, the script will generate a `base.json` file in the working directory. This file contains all the detailed calculation data extracted from the archives.

The base.json file has the following structure for each material:

```json
{
  "mc3d-id": {
    "elastic": {
      "<pseudopotential>": {
        "born": {
          "<qdensity>": {
            "VRH_average": {
              "bulk_modulus": 186.520654,
              "debye_temp": 245.351103,
              "lame_1st_para": 165.908422,
              "lame_2nd_para": 30.918348,
              "melting_temp": 2341.642084,
              "min_kappa": 0.724585,
              "modified_pettifor_ratio": 0.72139988,
              "p_wave_modulus": 227.745119,
              "pettifor_ratio": 1.53081493,
              "poisson_ratio": 0.421458,
              "pugh_ratio": 0.16576367,
              "shear_modulus": 30.918348,
              "sound_vel_LA": 5.179242,
              "sound_vel_TA": 1.908314,
              "sound_vel_bulk": 4.68711,
              "sound_vel_mean": 2.16656,
              "vickers_hardness": [
                { "H_1a": 17.961939 },
                { "H_1b": 4.560456 },
                { "H_1c": 5.344215 },
                { "H_2": 2.570456 },
                { "H_3": 5.58154 },
                { "H_4": 3.435372 },
                { "H_5": 2.202449 }
              ],
              "young_modulus": 87.898265
            },
            "elastic_constants": [
              [234.8494205, 162.356271, 162.356271, 0.0, 0.0, 0.0],
              [162.356271, 234.8494205, 162.356271, 0.0, 0.0, 0.0],
              [162.356271, 162.356271, 234.8494205, 0.0, 0.0, 0.0],
              [0.0, 0.0, 0.0, 27.80029448, 0.0, 0.0],
              [0.0, 0.0, 0.0, 0.0, 27.80029448, 0.0],
              [0.0, 0.0, 0.0, 0.0, 0.0, 27.80029448]
            ],
            "reuss_average": {
              "bulk_modulus": 186.520654,
              "debye_temp": 244.336054,
              ...
            },
            "voigt_average": {
              "bulk_modulus": 186.520654,
              "debye_temp": 246.361624,
              ...
            }
          }
        },
        "fd": {
          "VRH_average": {
            "bulk_modulus": 168.449956,
            "longitudinal_modulus_L": 1927.54662,
            "modified_pettifor_ratio": 0.74679294,
            "pettifor_ratio": 2.39649168,
            "poisson_ratio": 0.43984,
            "pugh_ratio": 0.10821,
            "shear_modulus": 18.22853,
            "young_modulus": 52.492249
          },
          "elastic_constants": [
            [239.5600728, 132.8948969, 132.8948969, 0.0, 0.0, 0.0],
            [132.8948969, 239.5600728, 132.8948969, 0.0, 0.0, 0.0],
            [132.8948969, 132.8948969, 239.5600728, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 7.09765889, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 7.09765889, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 7.09765889]
          ],
          "reuss_average": {
            "bulk_modulus": 168.449956,
            "modified_pettifor_ratio": 0.74679294,
            ...
          },
          "structure_uuid": "20dcccf3-417b-4f8e-8cd2-e46ee8f1959b",
          "voigt_average": {
            "bulk_modulus": 168.449956,
            "modified_pettifor_ratio": 0.74679294,
            ...
          }
        }
      }
    }
  }
}
```

## Organization of the MC3D discover website:

### **meta info**

The `meta.json` contains list of property columns for the MC3D landing page.

**SSSP**

We have 3 levels of qpoints_density, I have selected the successful MatdynBaseWorkChains with stable phonons (>5cm$^{-1}$) from the paper/workchains/phbands-qe/{qpoints_density}/matdyn groups:

- |q| = 0.3, here there are 198 stable phonons,
- |q| = 0.5, here there are 587 stable phonons,
- |q| = 0.7, here there are 2715 stable phonons,

We have 264 materials from the finite-displacement calculations.

**PseudoDojo**

We have 298 materials from the finite-displacement calculations.

We have 290 materials from the Born approximation.


- 