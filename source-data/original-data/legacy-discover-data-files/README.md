# 2D materials Discover section data

This repository contains the data served by the Materials Cloud REST API
and which is used for the index and detail pages of the 2D materials 
Discover section.

The `2d_index.json` and `2d_data.json` files were generated using the
``create_index.py`` script.
The original data come from the JSON files ``materials_cloud_2D_EE_less6atoms.json``
(prepared by N. Mounet and used for the first version of the 2D structures Discover section),
``MC_olddb_merged_noph.json`` and ``MC_newdb_merged.json``
(prepared by D. Campi, containing all old database properties without phonons and all the
properties of the new database respectively).

Once D. Campi publishes his work on phonons, the ``MC_olddb_merged_noph.json``
has to be substituted with the ``MC_olddb_merged.json``
in the ``create_index.py`` script, and the script has to be re-run to
generated the JSON files updated with the phonon information.

The JSON files ``nodes_to_delete_new_db_all_141221.json`` and ``uuids_to_be_removed_from_2D_old_db.json``
contain the UUIDs of nodes containing licensed data (crystal structures from ICSD
or MPDS) and were removed from the database using the script ``delete_nodes.py``.

The ``PhViz_data`` folder contains the JSON files used for the phonons. They are extracted from the out-phonons.tar.gz archive, which contains also other files with UUID information and raw QE files.
The phonon files were re-computed in September 2021 by Giovanni Pizzi using [this script](https://github.com/materialscloud-org/tools-phonon-dispersion/blob/e679191f2689be137f52cd54909e7be490d88225/misc/data-from-2d-MC-discover/get-data-from-mc-discover.py),
which fetches all data via the REST API and does not require to have AiiDA.

## Notes

To be able to conveniently keep track on how the files change over time, use `python -m json.tool --sort-keys file.json`.