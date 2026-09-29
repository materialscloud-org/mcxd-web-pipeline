# The `mc3d/pbesol-v1/mechanical` Dataset Generation Script

This code `scripts/gen.py` extracts mechanical results and generates a derived `base.json` for the MC3D Discover deployment.

### 📋 **Prerequisites**

Before running the script, you will need:

1. **AiiDA Environment**: This script requires a working AiiDA environment (e.g., with `aiida-core` installed).

2. **Mechanical archive**: Download `elastic.aiida` from the [mechanical Materials Cloud archive](https://doi.org/10.24435/materialscloud:3m-0e).

3. **Superconductivity archive**: This dataset leans on the [MC3D superconductivity dataset](https://doi.org/10.24435/materialscloud:n9-a7). Download its `EPW-screening.aiida` archive as well, or import both datasets into the same AiiDA profile.

## 🚀 Usage

The archive- and profile-based builds always load superconductivity data and calculate the `c` descriptor. It fails before writing an output file if that data is unavailable.

### Minimal archive-based build

Pass both required AiiDA archives explicitly:

```bash
python3 scripts/gen.py \
  --elastic-file "/path/to/elastic.aiida" \
  --supercon-file "/path/to/EPW-screening.aiida" \
  --output /tmp/mechanical-base.json
```

The generated file is intentionally written to the explicit `--output` path. Existing files are protected; use `--force` only when deliberately replacing a reviewed output.

### **Option 1: Using an AiiDA Profile**

If both datasets have already been imported into one AiiDA profile, specify that profile directly:

```bash
python3 scripts/gen.py --profile "YOUR_PROFILE_NAME" --output /tmp/mechanical-base.json
```


## 💾 Output

`base.json` is derived data, not a source of record. Review the generated file before intentionally replacing the versioned deployment file. The script never writes `meta.json`.

`meta.json` is the small, versioned frontend schema that declares the indexed columns. It cannot be inferred safely from archive contents, so use the checked-in `meta.json` for this dataset and change it only when the frontend schema itself changes. Recreating the deployment inputs therefore means generating `base.json` with this script and retaining the matching versioned `meta.json`.

The base.json file has the following structure for each material:

```json
{
  "mc3d-id": {
    "elastic": {
      "Born": {
        "<pseudopotential>": {
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
          "<pseudopotential>": {
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
}
```

pseudopotential can be "SSSP" or "Pseudodojo".
qdensity can be "0.3", "0.5", "0.7" or "fd".

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
| `longitudinal_modulus_L` | $L$ | Longitudinal modulus | GPa |  |
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

Form of the elastic constant table:

Elastic constant $ \sigma_{i}=C_{ij}  \epsilon_{j}$:
| $C_{ij}$ | $\epsilon_{1}$ | $\epsilon_{2}$ | $\epsilon_{3}$ | $\epsilon_{4}$ | $\epsilon_{5}$ | $\epsilon_{6}$ |
|---|---|---|---|---|---|---|
| $\sigma_{1}$ | $C_{11}$ | $C_{12}$ | $C_{13}$ | $C_{14}$ | $C_{15}$ | $C_{16}$ |
| $\sigma_{2}$ | $C_{12}$ | $C_{22}$ | $C_{23}$ | $C_{24}$ | $C_{25}$ | $C_{26}$ |
| $\sigma_{3}$ | $C_{13}$ | $C_{23}$ | $C_{33}$ | $C_{34}$ | $C_{35}$ | $C_{36}$ |
| $\sigma_{4}$ | $C_{14}$ | $C_{24}$ | $C_{34}$ | $C_{44}$ | $C_{45}$ | $C_{46}$ |
| $\sigma_{5}$ | $C_{15}$ | $C_{25}$ | $C_{35}$ | $C_{45}$ | $C_{55}$ | $C_{56}$ |
| $\sigma_{6}$ | $C_{16}$ | $C_{26}$ | $C_{36}$ | $C_{46}$ | $C_{56}$ | $C_{66}$ |