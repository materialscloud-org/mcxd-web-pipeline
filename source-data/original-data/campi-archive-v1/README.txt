Summary of README.txt:
- HOW TO CITE
- CONTENTS
- HOW TO READ DATA
- HOW TO IMPORT/VISUALIZE THE STRUCTURES
- HOW TO IMPORT THE DATABASE WITH AIIDA
- ABBREVIATIONS
- UNITS
- EXTERNAL REFERENCES


================================


This repository contains 3077 two-dimensional crystal structures (given with lattice vectors, atomic species and positions), exfoliated from three-dimensional experimental crystal structures. 2742 of these structures have been relaxed at the DFT-PBE level. Together with each structure, a set of materials properties is also given (at the DFT-PBE level): chemical formula, spacegroup, structural prototype, and for a subset of 2345 materials also band-gap and electronic bands. All the calculations (relaxation of the 3D parent, optimization of the 2D monolayer and band structures) are done neglecting any possible magnetic ordering and trateing all the materials as spin unpolarized. 


================================
HOW TO CITE
================================


If you use these data for publication purposes, please cite:
* D.campi, N. Mounet, M. Gibertini, G. Pizzi, N. Marzari, ArXiv XX.XX[a]


================================
CONTENTS
================================


as_extracted_2d_structures[b]/*.xsf               - 3077 2D structures as extracted from the 3D parent (i.e. not optimized as isolated monolayers) in XSF format for viewing using XCrySDen
as_extracted_2d_structures/*.cif                  - 3077 2D structures as extracted from the 3D parent (i.e. not optimized as isolated monolayers) in CIF format 
optimized_2d_structures/*.xsf                     - 2742 2D structures geometrically optimized as isolated monolayers using PBE functional in XSF format for viewing using XCrySDen
optimized_2d_structures/*.cif                     - 2742 2D structures geometrically optimized as isolated monolayers using PBE functional in CIF format
bands/*.agr                                       - 2345 electronic band structure plots in xmgrace format
lattice_matching/*.json                           - 606 json dictionaries containing the information on the lattice matching 
README.txt                                        - this README file
LICENSE.txt                                       - LICENSE information
structures.json                                   - data for all the properties of the 3077 2D structures, in JSON format
MC2D_export_20220622.aiida                        - full database and its provenance, in the form of an AiiDA [1] export file (generated with AiiDA v2.0.1). 
                                                    Note that the ICSD and MPDS initial structures are protected by copyright and were therefore not included.
supplementary_materials_ee_le6.pdf                -PDF file summarizing the properties of the easily exfoliable materials with up to 6 atoms in the unit cell.
supplementary_materials_pe_le6.pdf                -PDF file summarizing the properties of the potentially exfoliable materials with up to 6 atoms in the unit cell.



================================
HOW TO READ DATA
================================


The JSON file "structure_2d.json" contains a list where each element represents a dictionary with all the computed properties of a given 2D structure. 


The file could be read using any JSON parsing tool. For example, in Python:

import json
with open('structure_2d.json') as f:
    structures = json.load(f)


As an example, structures[0] looks like:


{u'abundance': 5.0000000000000004e-08,
 u'all_3D_parents': [{u'binding_energy_per_substructure_per_unit_area_df2': {u'key': u'binding_energy_per_substructure_per_unit_area',
    u'uuid': u'bd666977-a210-457f-a860-2b1a9211b8a3',
    u'value': 0.0149816350662265},
   u'db_id': u'263061',
   u'formula': u'Zn2In4Se8O24',
   u'source_db': u'ICSD',
   u'spg': u'P2_1/c',
   u'uuid': u'bea3c00d-bb9d-4c81-a06d-e18145efe657'}],
 u'as_extracted_2D_structure_uuid': u'47e2d50c-9387-4500-aab8-97bffca3fce6',
 u'band_gap': {u'key': u'band_gap',
  u'uuid': u'f14bb2a8-9d7c-4727-9570-ee071f6e7531',
  u'value': 4.006325670648691},
 u'bands_uuid': u'019ef4b9-b184-4643-9fb7-fa21c8d3a058',
 u'binding_energy_per_substructure_per_unit_area_df2': {u'key': u'binding_energy_per_substructure_per_unit_area',
  u'uuid': u'bd666977-a210-457f-a860-2b1a9211b8a3',
  u'value': 0.0149816350662265},
 u'formula': u'ZnIn2Se4O12',
 u'initial_3D_bulk_structure_uuid': u'bea3c00d-bb9d-4c81-a06d-e18145efe657',
 u'initial_3D_db_id': u'263061',
 u'initial_3D_formula': u'Zn2In4Se8O24',
 u'initial_3D_source_db': u'ICSD',
 u'initial_3D_spg': u'P2_1/c',
 u'number_of_atoms': 38,
 u'number_of_species': 4,
 u'optimized_2D_structure_uuid': u'47df4485-5c81-4597-921b-70f06df6a848',
 u'point_group': u'm',
 u'prototype': u'In2O12Se4Zn',
 u'relaxed_3D_bulk_structure_df2_uuid': u'098afd24-f620-4c5d-9bf6-47276c13219c',
 u'space_group': u'Pc (7)'}




A few remarks:
* All the keys ending with 'uuid' provide the unique identifier (UUID) of the corresponding AiiDA object (see below).
* The key 'db_id' specifies the id number of the 3D parent structure(s) in the source database, the latter
  being either the MPDS, ICSD or COD as indicated by the key 'source_db'. In the case of the ICSD, this id 
  number refers to the "ICSD Collection Code".
* The key 'as_extracted_2D_structure_uuid' gives the uuid of the 2D monolayer as extracted from the 3D parent
  without further optimization as an isolated monolayer. The uuid can be used directly in AiiDA if the full database 
  has been imported or it can be used to find the proper structure in the folder "as_extracted_2d_structures" in which
  structures are named accordingly to this uuid.
* The key 'optimized_2D_structure_uuid' gives the uuid of the 2D monolayer optimized with a variable cell relaxation as an 
  isolated monolayer using the PBE functional. The uuid can be used directly in AiiDA if the full database 
  has been imported or it can be used to find the proper structure in the folder "optimized_2d_structures" in which
  structures are named accordingly to this uuid.
* The key 'bands_uuid' gives the first part of the name of the files containing the electronic bands along high-symmetry paths
  contained in the folder "bands" in xmgrace format (*.agr file extension). The zero is always set at the Fermi level.
* The key 'all_3D_parents' gives the list of 3D parents, sorted by binding energies (computed with the DF2-C09 
  functional) in ascending order (i.e. the lowest binding energy first).
* The key 'abundance' indicates the abundance in the Earth's crust of the least abundant element in the structure.
* The keys 'binding_energy_per_substructure_per_unit_area_df2' or 'binding_energy_per_substructure_per_unit_area_rvv10' contain 
  the value of the binding energy in eV/Ang^2 for the more favorable 3D parent computed respectively with the RVV10 or vdw-df-c09 
  functional. The uuid of the calculation is also reported. 
* The key 'band_gap' indicates the electronic band gap computed from the band structure along a proper high-symmetry path. The value is given in eV. 
  The uuid of the inline calculation used to compute the gap is also reported. 




So, in the example above:
* the structure as extracted from the 3D parent can be found in as_extracted_2D_structure_uuid/47e2d50c-9387-4500-aab8-97bffca3fce6.xsf, or as_extracted_2D_structure_uuid/47e2d50c-9387-4500-aab8-97bffca3fce6.cif
* the structure optimized as an isolated monolayer can be found in optimized_2d_structures/47df4485-5c81-4597-921b-70f06df6a848.xsf, optimized_2d_structures/47df4485-5c81-4597-921b-70f06df6a848.cif
* the bands can be found in bands/019ef4b9-b184-4643-9fb7-fa21c8d3a058.agr


The jsons contained in the lattice_matching folder are named as "lattice_match_uuid_of_the_optimized_structure.json" 
the json contains a dictionary whose keys are the uuids of the other optimized structures to which the structure that gives the name to the file is matched.
For each key in the dictionary there is a list of possible lattice matchings with different maximal strains allowed. Each element of the list has the format like: 




[{u'formula1': u'Ba2Ge2Mn2',
  u'formula2': u'As2O3',
  u'i11': 0,
  u'i12': -7,
  u'i21': -3,
  u'i22': -3,
  u'j11': -4,
  u'j12': 0,
  u'j21': -3,
  u'j22': 3,
  u'natoms': 258,
  u'strain': 0.0049108020424955675,
  u'surf_ratio_1': 28,
  u'surf_ratio_2': 18,
  u'uuid1': u'00676f04-8b2c-4eac-be95-86f49c9bd268',
  u'uuid2': u'de5d09ce-bf2d-4ba9-87d7-f342b2a2a636'},...]
  
  where "formula1" and "formula2" are the formulas of the two compounds being matched, "natoms" is the total number of atoms in the resulting supercell, "strain" is the global strain applied to, "surf_ratio_*" are the size of the supercell used in the match for each of the 2 compounds, i11,i12,i21,i22 (j11,j12,j21,j22) are the indices for each component of the two 2d vectors that define the first (second) supercell as defined in Ref.[6]
  
  


=======================================
HOW TO IMPORT/VISUALIZE THE STRUCTURES
=======================================


You can use XCrySDen [4] to visualize the structures in the .xsf format.


You can also use ASE [3] to import/manipulate the structures, within a Python
shell, in the following way:


* make sure ASE is installed:


pip install ase=3.12.0


* open e.g. an ipython shell:


ipython




from ase.io import read
structure_ase = read('optimized_2d_structures/47df4485-5c81-4597-921b-70f06df6a848.xsf')


* you can also visualize it using the ASE viewer:


from ase.visualize import view
view(structure_ase)


* in addition, if you are using AiiDA [1], from a verdi shell you can also directly convert the ASE structure into an AiiDA one:


from ase.io import read
StructureData = DataFactory('structure')
structure = StructureData(ase=read('optimized_2d_structures/47df4485-5c81-4597-921b-70f06df6a848.xsf'))


======================================
HOW TO IMPORT THE DATABASE WITH AIIDA
======================================


For AiiDA [1] users, the full database and its provenance is provided as an AiiDA export file.
To import the 2D database into your AiiDA db:


* Follow the instruction found at https://aiida.readthedocs.io/projects/aiida-core/en/v2.0.1/intro/get_started.html to install AiiDA and https://aiida.readthedocs.io/projects/aiida-core/en/v2.0.1/intro/installation.html for creating a new profile


* import the database:
verdi -p <YOUR_PROFILE> archive import two_dimensional_database.aiida


Then you can load within a 'verdi -p <YOUR_PROFILE> shell' any object referenced by its UUID given in the 
json file 'structures.json' (see above), using the command:


load_node(<UUID>)


You can also display a number of groups containing e.g. all the 2D relaxed structures, the 2D bands, etc.
with the command-line instruction:


verdi -p <YOUR_PROFILE> group list -c two_dimensional_database -A


which should list the groups listed below. These groups respectively contain (the type of the objects in the group is indicated between parentheses):
* expanded_two_dimensional_database_intial_2D_structures_as_extracted_from_3D_parent (StructureData)
* expanded_two_dimensional_database_pw_scf_relaxed_2D_structures_pbe (PwCalculation)
* expanded_two_dimensional_database_bands_relaxed_2D_structures_pbe (BandsData)
* expanded_two_dimensional_database_binding_energies_from_all_3D_parents (ParameterData)


the group: 
"expanded_two_dimensional_database_intial_2D_structures_as_extracted_from_3D_parent" contains the structures as extratced 
from the bulk 3D.
 
the group:
"expanded_two_dimensional_database_pw_scf_relaxed_2D_structures_pbe" contains the PwCalculation corresponding to 
final SCF after the variable-cell optimization as an isolated monolayer.


the group:
"expanded_two_dimensional_database_bands_relaxed_2D_structures_pbe" contains the BandsData with the electronic band structure
at the PBE level.


the group: 
"expanded_two_dimensional_database_binding_energies_from_all_3D_parents" contains all the binding energies computed from 
the 3D bulk structures that turned out to be exfoliable. 






================================
ABBREVIATIONS
================================


- be -> binding energy,
- db -> database,
- spg -> spacegroup,
- df2 -> DF2-C09 van-der-Waals functional (see main journal reference and references therein),
- rvv10 -> rVV10 van-der-Waals functional (see main journal reference and references therein).


================================
UNITS
================================


- Binding energies: meV/angstrom^2,
- Band gaps: eV,
- Structural parameters (cell & atomic positions): angstrom.




================================
EXTERNAL REFERENCES
================================


[1] G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari and B. Kozinsky, 
    Comput. Mater. Sci. 111, 218 (2016)[f], http://www.aiida.net;
    S.P. Huber, et al. Scientific Data 7, 300 (2020).
[2] J. D. Hunter, Comput. Sci. Eng., 9, 3 (2007), 90-95, https://matplotlib.org
[3] A. H. Larsen, J. J. Mortensen, J. Blomqvist, I. E. Castelli, R. Christensen, et al,
    J. Phys.: Condens. Matter, 29, 273002 (2017), https://wiki.fysik.dtu.dk/ase/
[4] A. Kokalj, Comput. Mater. Sci. 28, 155 (2003) , http://www.xcrysden.org/
[5] P. Giannozzi et al., J.Phys.: Condens.Matter 21, 395502 (2009), http://dx.doi.org/10.1088/0953-8984/21/39/395502
the relaxation input parameters can be found in Q
[6] P. Lazić, Computer Physics Communications 197 (2015) 324–334.


[a]Write only "submitted (2022)" for now, we'll put the final citation later
[b]Here/below: mention it's a .zip file
[c]Which DOI is this?
[d]ADD PDF and other files (if they are added to the entry)
[e]This needs to be fixed?
[f]Add also second paper
