# Source metadata for MC2D

The MC2D consists of multiple different AiiDA databases and the metadata originally there didn't exist a single unified and consistent metadata file. This folder contains the effort to try to create a file like this:

```
mc2d-data.json
```

This file was created based on

- the raw MC2D AiiDA database on `prnmarvelsrv3`;
- the supplementary metadata file `structure_2d.json` in https://archive.materialscloud.org/record/2022.84;
- the various metadata files generated just for the legacy MC2D discover section (see the `legacy` branch);

The analysis, consistency checks and data validation is in `analysis.ipynb`. It was run on the `prnmarvelsrv3` but should also work for an AiiDA profile with the latest mc2d .aiida archive imported. Note that the notebook also contains code to generate a new and consistent version for https://archive.materialscloud.org/record/2022.84.

## Add AiiDA metadata

The `aiida-meta-add` folder contains a script that adds

1. `final_structures` group (matches with the frontend, used e.g. in the optimade pipeline);
2. `mc2d_id` extras for structures. Again, used for OPTIMADE.
