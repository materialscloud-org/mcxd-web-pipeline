# 2D topological insulators

This folder consists of the raw and formatted data for migrating the [2dtopo data](https://github.com/materialscloud-org/discover-2dtopo-data) section inside of MC2D. Most of the information for a particular material is already handled by the core contribution. Therefore we need to add;

- SOC (Spin orbit coupling) information;
- Missing phonons for materials
- HWCC tracking information (used for HWCC plotting)

## HWCC Tracking information

The hwcc tracking information is stored inside a z2pack json file /2dtopo/original_data, this has been reduced into simplified json;

```json
hwcc: {
  "k": [n], // x positions of each point, *note this isnt uniform
  "wcc": [m[n]], // yvalues of each point
  "gaps": [] // the  mid-point maximum wrapped distance at a given x (plotted in red)
}
```

| Info                           | Path                          |
| ------------------------------ | ----------------------------- |
| Original datafiles             | /original_data/hwcc_json/...  |
| Original plots png             | /original_data/hwcc_plots/... |
| New datafiles (webready)       | /data/hwcc_json/              |
| Script: (_visualise old data_) | /old/plot_hwcc.py             |
| Script: (_old data -> new_)    | /scripts/format_hwcc.py       |
| Script: (_visualise new data_) | /scripts/plot_hwcc            |

_Note: not all of the materials have hwcc plots, as some were computed with parity_eigv!_

## Metadata and mapping

The original metadata seems to be just written in line across two files `original_data/2dtopo_data.json` and `original_data/2dtopo_index.json` and hardcoded.

By inspection there seems to be some inconsistancies with MC2D;

the material AsCuLi2, has a `db_id:1535858, ICSD`, the equivalent entry is `mc2d-1288` which states the correct id: `db_id:43938, ICSD`.

Further investigation suggests that actually all the data might be there, just some fields are swapped between materials. Some manual work has been performed to correct this, with MC2D being the source of truth.

| Material    | Equivalent MC2D Material                                         |
| ----------- | ---------------------------------------------------------------- |
| Pt2HgSe3    | [mc2d-400](https://mc2d.materialscloud.org/#/details/mc2d-400)   |
| WTe2        | [mc2d-255](https://mc2d.materialscloud.org/#/details/mc2d-255)   |
| RhTaTe4     | [mc2d-488](https://mc2d.materialscloud.org/#/details/mc2d-488)   |
| AsCuLi2     | [mc2d-1288](https://mc2d.materialscloud.org/#/details/mc2d-1288) |
| MoTe2       | [mc2d-206](https://mc2d.materialscloud.org/#/details/mc2d-206)   |
| TiCu2Te3    | [mc2d-864](https://mc2d.materialscloud.org/#/details/mc2d-864)   |
| IrNbTe4     | [mc2d-396](https://mc2d.materialscloud.org/#/details/mc2d-396)   |
| ZrBr        | [mc2d-70](https://mc2d.materialscloud.org/#/details/mc2d-70)     |
| Bi          | [mc2d-18](https://mc2d.materialscloud.org/#/details/mc2d-18)     |
| TiNI        | [mc2d-192](https://mc2d.materialscloud.org/#/details/mc2d-192)   |
| In2ZnS4     | [mc2d-567](https://mc2d.materialscloud.org/#/details/mc2d-567)   |
| TaIrTe4     | [mc2d-706](https://mc2d.materialscloud.org/#/details/mc2d-706)   |
| ZrCl        | [mc2d-126](https://mc2d.materialscloud.org/#/details/mc2d-126)   |
| Pd2HgSe3    | no matching mc2d                                                 |
| Fe4O6       | [mc2d-2337](https://mc2d.materialscloud.org/#/details/mc2d-2337) |
| Mo2O17Ta2   | [mc2d-2315](https://mc2d.materialscloud.org/#/details/mc2d-2315) |
| C2H6Fe2O8P2 | [mc2d-1956](https://mc2d.materialscloud.org/#/details/mc2d-1956) |
| Br6V2       | [mc2d-2312](https://mc2d.materialscloud.org/#/details/mc2d-2312) |
| Hf2Te10     | [mc2d-1775](https://mc2d.materialscloud.org/#/details/mc2d-1775) |
| Hg4N4S4     | [mc2d-2366](https://mc2d.materialscloud.org/#/details/mc2d-2366) |
| Te10Zr2     | [mc2d-2514](https://mc2d.materialscloud.org/#/details/mc2d-2514) |
| Cl2Hf2      | [mc2d-2474](https://mc2d.materialscloud.org/#/details/mc2d-2474) |
| Br2Hf2      | [mc2d-2291](https://mc2d.materialscloud.org/#/details/mc2d-2291) |
| I4Mo2S4     | [mc2d-1839](https://mc2d.materialscloud.org/#/details/mc2d-1839) |
| BaCr2N2O8   | [mc2d-2352](https://mc2d.materialscloud.org/#/details/mc2d-2352) |

A intermediate formatted metadata script has been used to generate "/data/2dtopo_base.json",
