# 2D altermagnets

This folder contains the source and formatted data for a high-throughput study of two-dimensional altermagnets contributed to MC2D. The supplied dataset contains 23 materials. Records are associated with the MC2D core contribution through their MC2D identifiers; this section adds the following calculated properties and provenance references:

- Self-consistent Hubbard U values.
- Maximum spin splittings and maximum spin splittings near the Fermi level.
- Electronic band gaps of the reported altermagnetic states.
- Energy differences relative to competing magnetic states, normalized per magnetic atom.
- Sampled Hubbard U values for which altermagnetism was reported.
- UUIDs of the altermagnet and bands workflows.

## Contribution details

This section contains the results supplied for the 2D altermagnetism contribution. The scientific methodology is described in `METHODOLOGY.md`.

Please cite A. Bose, N. Manko, M. Gibertini, and A. Marrazzo, [*Symmetry-Guided Computational Screening of Two-Dimensional Altermagnets with ab initio Hubbard Corrections*](https://arxiv.org/abs/2608.02925v1), arXiv:2608.02925v1 (2026). The manuscript also lists *2D altermagnets database*, Materials Cloud (2026).

## Altermagnetism data

The source export is a JSON list containing one record per material. The generation script converts it into a JSON object keyed by MC2D ID, as required for `base.json`.

| Property | Field in `base.json` | Unit |
| --- | --- | --- |
| Chemical formula | `chemical_formula` | — |
| Space-group symbol | `space_group_symbol` | — |
| Space-group number | `space_group_number` | — |
| Self-consistent Hubbard U | `self_consistent_hubbard_U_eV` | eV |
| Maximum spin splitting | `maximum_splitting_meV` | meV |
| Maximum spin splitting near the Fermi level | `maximum_splitting_near_E_F_meV` | meV |
| Band gap | `band_gap_eV` | eV |
| Magnetic energy difference | `delta_E_min_AM_NAM_meV_per_magnetic_atom` | meV/magnetic atom |
| Competing magnetic-state label | `competing_magnetic_state` | — |
| Sampled U values yielding altermagnetism | `AM_for_U_values_eV` | eV |
| Altermagnet workflow UUID | `altermagnets_workchain_uuid` | — |
| Bands workflow UUID | `pw_bands_workchain_uuid` | — |

The numerical results are preserved as supplied, without unit conversion or energy-sign changes. Maximum splitting covers the full 2D Brillouin zone and all included electronic states. Near-Fermi splitting refers to the highest occupied states for insulators and partially occupied states for metals, with the insulating reference at the valence-band maximum. It is not defined by an invented fixed energy window. See `METHODOLOGY.md` for the scientific procedure and `REVIEW_NOTES.md` for the revision history and remaining integration details.

The U-value array records discrete sampled values; it does not define a continuous interval. FM and AFM are the supplied competitor labels. A non-altermagnetic competitor is not necessarily nonmagnetic. Reported zero energy differences are retained at their supplied precision.

The five numerical index columns in `meta.json` are Hubbard U, maximum splitting, near-Fermi splitting, band gap, and magnetic energy difference. Their `data_path` values match the corresponding keys in each material record. The proposed `am_` data labels require frontend integration review.

## Files and scripts

Paths below are relative to this contribution folder.

| Information | Path |
| --- | --- |
| Original results export | `original_data/altermagnets_data.json` |
| Generated per-material data | `base.json` |
| Landing-page column metadata | `meta.json` |
| Data-generation script | `scripts/gen.py` |
| Scientific methodology | `METHODOLOGY.md` |
| Detail-page description | `description.md` |
| Citation metadata | `citation.json` |
| Publications footer | `contribution.md` |

## Metadata and mapping

The following mappings are taken from the supplied results export. They have not been independently checked against the MC2D structures. Formula labels alone do not establish that the calculated structure or magnetic supercell matches a database entry.

| Material | MC2D entry |
| --- | --- |
| Fe2SeTe | [mc2d-1823](https://mc2d.materialscloud.org/#/details/mc2d-1823) |
| CoBrO | [mc2d-2502](https://mc2d.materialscloud.org/#/details/mc2d-2502) |
| CuH8N2(OF2)2 | [mc2d-1726](https://mc2d.materialscloud.org/#/details/mc2d-1726) |
| Fe2Si2SbO9 | [mc2d-2545](https://mc2d.materialscloud.org/#/details/mc2d-2545) |
| NiH2C2N3Cl | [mc2d-1679](https://mc2d.materialscloud.org/#/details/mc2d-1679) |
| SrCo2Te3(ClO4)2 | [mc2d-783](https://mc2d.materialscloud.org/#/details/mc2d-783) |
| MnH2C2N3Cl | [mc2d-391](https://mc2d.materialscloud.org/#/details/mc2d-391) |
| CoMoTeO6 | [mc2d-1160](https://mc2d.materialscloud.org/#/details/mc2d-1160) |
| MnMoTeO6 | [mc2d-273](https://mc2d.materialscloud.org/#/details/mc2d-273) |
| CoH8N2(OF2)2 | [mc2d-1729](https://mc2d.materialscloud.org/#/details/mc2d-1729) |
| RuF4 | [mc2d-1509](https://mc2d.materialscloud.org/#/details/mc2d-1509) |
| ReCl3 | [mc2d-1326](https://mc2d.materialscloud.org/#/details/mc2d-1326) |
| CuSe2O5 | [mc2d-1482](https://mc2d.materialscloud.org/#/details/mc2d-1482) |
| CuP2(HO)4 | [mc2d-978](https://mc2d.materialscloud.org/#/details/mc2d-978) |
| NiPH4ClO3 | [mc2d-683](https://mc2d.materialscloud.org/#/details/mc2d-683) |
| V4S9Br4 | [mc2d-1204](https://mc2d.materialscloud.org/#/details/mc2d-1204) |
| V3(H3O5)2 | [mc2d-1568](https://mc2d.materialscloud.org/#/details/mc2d-1568) |
| CoH4(NO4)2 | [mc2d-539](https://mc2d.materialscloud.org/#/details/mc2d-539) |
| AgRuF7 | [mc2d-1025](https://mc2d.materialscloud.org/#/details/mc2d-1025) |
| Al2CuCl8 | [mc2d-456](https://mc2d.materialscloud.org/#/details/mc2d-456) |
| CuH4C6S(NCl)2 | [mc2d-2650](https://mc2d.materialscloud.org/#/details/mc2d-2650) |
| CuH6(CN2)4 | [mc2d-727](https://mc2d.materialscloud.org/#/details/mc2d-727) |
| VF4 | [mc2d-1010](https://mc2d.materialscloud.org/#/details/mc2d-1010) |

For ReCl₃ (mc2d-1326), the unavailable pw_bands_workchain_uuid is represented as null in base.json. The workflow UUIDs identify calculation workflows, rather than their output bandstructure nodes.

## Generating base.json

Place this folder at `mc2d-data/data/<version>/altermagnetism/`, after confirming the version and section name with the maintainers. From inside the contribution folder, run:

```sh
python3 scripts/gen.py
```

The script uses the Python standard library. `gen.py` reads `original_data/altermagnets_data.json`, rejects duplicate or malformed MC2D IDs, removes the redundant inner `mc2d-ID` field, converts missing UUID strings to null, and writes the MC2D-ID-keyed `base.json`. It formats the supplied export; it does not rerun calculations or extract results directly from AiiDA.

To regenerate from another export:

```sh
python3 scripts/gen.py --source /path/to/results.json --output /path/to/base.json
```

For the normal contribution workflow, update `original_data/altermagnets_data.json` and regenerate. **Do not hand-edit `base.json`.**
