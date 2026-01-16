# Phonon visualization data

To visualize the atomic displacements of phonons like in [tools-phonon-dispersion](https://github.com/materialscloud-org/tools-phonon-dispersion), what seems to be needed is

- phonon bands;
- phonon displacements;
- (metadata).

The MC2D AiiDA file contains phonon bands for many materials (245 from Mounet et al, and new ones from Campi et al), but it doesn't directly contain the displacements (and metadata), and therefore, this needs to be provided separately.

For the 245 materials of Mounet et al, all necessary files were generated in September 2021 by Giovanni with [this script](https://github.com/materialscloud-org/tools-phonon-dispersion/blob/e679191f2689be137f52cd54909e7be490d88225/misc/data-from-2d-MC-discover/get-data-from-mc-discover.py) and this data is included in `original-data/out-phonons.tar.gz`. The script seems quite complex, and seems to require calling Quantum Espresso, so it's not extended to the rest of the materials that have phonon bands calculated. In the current pipeline, we just get the data from this tar file and populate the MongoDB just for the 245 materials.

In the future, it would be great to generate the displacement data for all materials that include phonon calculations. Potentially with a simplified script included in this repo.
