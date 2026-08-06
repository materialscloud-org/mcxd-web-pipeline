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
            },
            "workchain_uuid": "53eb5c53-649b-41f1-9f8d-99f3b0b9007f"
          }
        },
        "FD": {
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
          },
          "workchain_uuid": "c878f6e3-1326-4992-9691-e126b3490152"
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

## Mechanical-property fields

The keys in `base.json` should be render using the following schema in the frontend.

Map each JSON key to:

- a mathematical symbol;
- a human-readable name;
- a physical unit;
- an appropriate numerical format.

The elastic moduli, elastic constants, and hardness values are expressed in GPa, temperatures in K, sound velocities in $km s^{\text{-1}}$, and thermal conductivity in $W m^{\text{-1}}K^{\text{-1}}$.

| JSON key | Display symbol | Property | Unit | Notes |
|---|---:|---|---:|---|
| `bulk_modulus` | $B$ | Bulk modulus | GPa | Isotropic bulk modulus. |
| `shear_modulus` | $G$ | Shear modulus | GPa | Isotropic shear modulus. |
| `young_modulus` | $E$ | Young's modulus | GPa | Isotropic Young's modulus. |
| `poisson_ratio` | $\nu$ | Poisson's ratio | dimensionless | No unit should be displayed. |
| `lame_1st_para` | $\lambda$ | First Lamé parameter | GPa | First Lamé coefficient. |
| `lame_2nd_para` | $\mu$ | Second Lamé parameter | GPa | Equivalent to the isotropic shear modulus. |
| `p_wave_modulus` | $M$ | P-wave modulus | GPa | For an isotropic medium, $M=\lambda+2\mu$. |
| `pugh_ratio` | $r^{\mathrm{Pugh}}$ | Pugh ratio | dimensionless | Defined here as $G/B$. |
| `pettifor_ratio` | $r^{\mathrm{Pett}}$ | Pettifor ratio | dimensionless | No unit should be displayed. |
| `modified_pettifor_ratio` | $\widetilde{r}^{\mathrm{Pett}}$ | Modified Pettifor ratio | dimensionless | Modified form of the Pettifor descriptor. |
| `debye_temp` | $\Theta^{\mathrm{D}}$ | Debye temperature | K | Estimated from the elastic and acoustic properties. |
| `melting_temp` | $T^{\mathrm{m}}$ | Melting temperature | K | Estimated melting temperature. |
| `min_kappa` | $\kappa^{\min}$ | Minimum thermal conductivity | $W / (m \cdot K)$ | Estimated minimum lattice thermal conductivity. |
| `sound_vel_LA` | $v^{\mathrm{LA}}$ | Longitudinal acoustic sound velocity | $km / s$ | Longitudinal acoustic mode. |
| `sound_vel_TA` | $v^{\mathrm{TA}}$ | Transverse acoustic sound velocity | $km / s$ | Transverse acoustic mode. |
| `sound_vel_bulk` | $v^{\mathrm{B}}$ | Bulk sound velocity | $km / s$ | Sound velocity derived from the bulk modulus. |
| `sound_vel_shear` | $v^{\mathrm{S}}$ | Shear sound velocity | $km / s$ | Sound velocity derived from the shear modulus. |
| `sound_vel_compressional` | $v^{\mathrm{P}}$ | Compressional sound velocity | $km / s$ | Sound velocity derived from the compressional modulus. |
| `sound_vel_mean` | $v^{\mathrm{m}}$ | Mean sound velocity | $km / s$ | Average acoustic velocity used, for example, in Debye-temperature estimates. |
| `vickers_hardness` | $H^{\mathrm{V}}$ | Vickers hardness | GPa | May contain several estimates. An empty array indicates that no estimate is available. |
| `elastic_constants` | $C_{ij}$ | Elastic stiffness constants | GPa | Stored as an elastic-stiffness matrix, normally in Voigt notation. |

### Frontend display convention

The frontend should display the mathematical symbol together with either the full property name or a tooltip. For example:

```text
B       38.80 GPa
G       24.53 GPa
ν       0.239
Θ_D     333.38 K
v_LA    4.75 km s⁻¹
```

A symbol should not normally be shown without a human-readable description, because symbols such as \(M\), \(B\), and \(G\) may be ambiguous outside their immediate context.

