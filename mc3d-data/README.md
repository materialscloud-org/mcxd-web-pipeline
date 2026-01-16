# Materials Cloud 3D Crystals Database (MC3D) web pipeline

This repository contains the pipeline (data and scripts) to collect curated data from various MC3D subdatabases and contributions, and populate one single MongoDB database of curated data. Note that this database itself is not a complete represetation of the MC3D, as it will contain links to the underlying AiiDA databases (in the form of UUIDs).

The data from this MongoDB is served via the Materials Cloud API (https://github.com/materialscloud-org/mc-rest-api), hosted at https://api.materialscloud.org/docs.

This API powers the MC3D frontend https://mc3d.materialscloud.org.

The MC3D consists of the following subdatabases:

- `mc3d/pbe-v1`
- `mc3d/pbesol-v1`
- `mc3d/pbesol-v2`

Each of the subdatabases consists of

- `base` contribution, containing
  1. optimized structures; and
  2. optionally also properties.
- and supplementary contributions, which
  - contain only properties for the structures in the `base` contribution,
  - (these contributions should not introduce new structures).

## Contributing data

The current data organization allows for supplementary property/calculation contributions only to existing structure subdatabases (e.g. `pbesol-v1`). This means that no new structures are allowed, and every contribution must be tied to a specific structure.

The standard contribution consists of an AiiDA archive (e.g. by uploading to Materials Cloud Archive) and a folder containg metadata files (e.g. in `/data/pbesol-v1/contrib-1/`) that can contain:

- `README.md` - Explanation of the contribution and links to any source information, especially AiiDA archive files.
- `base.json` - key-value data for each material, will be automatically added to the `/base` API endpoint. Can include AiiDA UUIDs. See the existing files for the format details.
- `meta.json` - any relevant "common" metadata, e.g. to define the columns to the materials index. Will be automatically added to the `\meta` API endpoint. See the existing files for format details.
- custom data files or subdirectories that supplement and/or document the data.

These data files are parsed by the scripts in `pipeline/` and populate the MC3D MongoDB. In order for any custom data to be available in the API, a custom pipeline script needs to be provided. See e.g. the `xrd` script that populates its own MongoDB collection.
