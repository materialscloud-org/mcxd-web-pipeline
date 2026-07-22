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
              ...
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
            ...
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

We have 3 levels of qpoints_density, we have:

- namespace=elastic.SSSP.born.0.3, for $|q| = 0.3$, here there are 198 stable phonons out of 578 successful workchains,
- namespace=elastic.SSSP.born.0.5, for $|q| = 0.5$, here there are 587 stable phonons out of 1380 successful workchains,
- namespace=elastic.SSSP.born.0.7, for $|q| = 0.7$, here there are 2715 stable phonons out of 4093 successful workchains,
- namespace=elastic.SSSP.fd, for finite-displacement calculations, we have 264 materials.

**PseudoDojo**

- namespace=elastic.PseudoDojo.born.0.5, we have 298 materials from the finite-displacement calculations.
- namespace=elastic.PseudoDojo.fd, we have 290 materials from the Born approximation at |q|=0.5.
