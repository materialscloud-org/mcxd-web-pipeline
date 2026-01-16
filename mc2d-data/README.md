# Materials Cloud 2D Crystals Database (MC2D) MongoDB pipeline

This repository contains the pipeline (data and scripts) to collect curated data from various MC2D contributions, and populate one single MongoDB database of curated data. Note that this database itself is not a complete represetation of the MC2D, as it will contain links to the underlying AiiDA databases (in the form of UUIDs).

Currently the only subdatabase is `mc2d/pbe-v1` and it consists of

- `base` contribution, containing
  1. optimized structures; and
  2. various properties.
- and supplementary contributions, which
  - contain only properties for the structures in the `base` contribution,
  - (these contributions should not introduce new structures).

Each contribution is contained in its own directory (see e.g. `/data/pbe-v1/`) and can contain the following:

- `README.md` - Explanation of the contribution and links to any source information, especially AiiDA archive files.
- `scripts/` - any scripts to either generate the data files or populate the MongoDB directly.
- `data.json` - data for each material.
- `meta.json` - any relevant metadata, e.g. to define the columns to the "global materials index".

These data files (and scripts) are parsed by the scripts in `pipeline/` and populate the MongoDB.

The API that serves this (and other) data is https://github.com/materialscloud-org/mc-rest-api.

Finally, Materials Cloud hosts a frontend to the MC2D based on the API at https://mc2d.materialscloud.org.
