# The `mc2d/pbe-v1` base dataset

This dataset is based on the following archive entry: https://archive.materialscloud.org/record/2022.84

Note that the AiiDA database also contains the initial contribution in https://archive.materialscloud.org/record/2020.158

The data of the main archive entry was not fully consistent, so the current version of this data is generated from a cleaned dataset which is currently unpublished.

## Note!

It seems that calculation of band gap is by some hidden function 'get_bandgap_inline' under aiida.workflows.user.epfl_theos.quantumespresso.helpers' ...
This seems to produce erroneous results when compared to other calculations (in particular 2dtopo)... (atleast w.r.t the fermi energy)

For now such problems have been ignored but some investigation is important.

_**example:** material 'mc2d-2514' states to have a bandgap of 0.061 eV but the resulting band structure plot shows no gap at 0 eV (and a small gap above 0)._
