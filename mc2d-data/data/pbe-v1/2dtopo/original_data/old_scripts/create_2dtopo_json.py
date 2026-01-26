#!/usr/bin/env python 
import matplotlib.pyplot as plt
import numpy as np
import sys, glob, re,subprocess
from ase.io import read
import json
data_dict = {}

#'Bi2'
data_dict['Bi'] = {'display_formula':'Bi',
                    'band_gap':545,
                    'space_group':r'P<SPAN STYLE="text-decoration:overline">3</SPAN>m1 (164)', #P${\bar{3}m1}$ (164)
                    'inversion_strength':685,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':18,
                    'binding_energy_per_substructure_per_unit_area_rVV10':25,
                    'atoms_per_cell':2,
                    'gw_inversion_strength':760,
                    'colors':{'Bi':'purple'},
                    'source_db':'ICSD',
                    'db_id':43938,
                    'Z_avg':83.0,
                    'band_structure_without_SOC':'997c796c-bcde-49a2-abb4-c9ae862346c7',
                    'fermi_without_SOC':-4.07738038470729,
                    'band_structure_with_SOC':'7e92c2f6-7f42-4f75-8879-7d100168602c',
                    'fermi_with_SOC':-3.89992197740684,
                    'phonons':'24f949ee-86ec-45aa-b947-8286ec7bdaad',
                    'structure':'443a4bf0-76c2-4000-97c6-e39f0c9ce91c',
                    }
#'AsCuLi2'
data_dict['AsCuLi2'] = {'display_formula':'AsCuLi2',
                    'band_gap':45,
                    'space_group':r'P<SPAN STYLE="text-decoration:overline">6</SPAN>m2 (187)', #'P${\bar{6}m2}$ (187)
                    'inversion_strength':80,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':63,
                    'binding_energy_per_substructure_per_unit_area_rVV10':62,
                    'atoms_per_cell':4,
                    'gw_inversion_strength':169,
                    'colors':{'Cu':'brown','Li and As':'purple'},
                    'source_db':'ICSD',
                    'db_id':153858,
                    'Z_avg':17.0,
                    'band_structure_without_SOC':'b934fb86-070d-4ff5-b565-91bb6375b7d1',
                    'fermi_without_SOC':-1.79718179030412,
                    'band_structure_with_SOC':'1996eabd-8724-4675-b088-6815d99763dc',
                    'fermi_with_SOC':-1.68326789113505,
                    'phonons':'221f7e1b-cc14-4cf1-b069-f2810544e610',
                    'structure':'c0b90825-7e3d-47d4-bc13-09d0d05c7fe1',
                    }
#I2N2Ti2
data_dict['TiNI'] = {'display_formula':'TiNI',
                    'band_gap':18,
                    'space_group':'Pmmn (59)',#P${mmn}$(59)
                    'inversion_strength':141,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':15,
                    'binding_energy_per_substructure_per_unit_area_rVV10':22,
                    'atoms_per_cell':6,
                    'gw_inversion_strength':'-705 (trivial)',
                    'colors':{'I':'purple','N':'blue', 'Ti':'grey'},
                    'source_db':'ICSD',
                    'db_id':27394,
                    'Z_avg':27.33,
                    'band_structure_without_SOC':'deabd65d-2d28-4bdd-90be-4c957933a47b',
                    'fermi_without_SOC':-5.42155915916908,
                    'band_structure_with_SOC':'a7898b56-4ff3-4c46-8c0b-947faff16a46',
                    'fermi_with_SOC':-5.35813718806538,
                    'phonons':'091792c8-8192-4252-9d1c-b86a7db97f22',
                    'structure':'4afd2627-5695-49ee-8e2f-2d1f49bff3bb',
                    }
#Ir2Nb2Te8
data_dict['IrNbTe4'] = {'display_formula':'IrNbTe4',
                    'band_gap':36,
                    'space_group':'Pm (6)',#P$m$ (6)
                    'inversion_strength':161 ,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':27,
                    'binding_energy_per_substructure_per_unit_area_rVV10':32,
                    'atoms_per_cell':12,
                    'colors':{'Ir':'dark blue','Nb':'blue','Te':'brown'},
                    'source_db':'ICSD',
                    'db_id':656451,
                    'Z_avg':54.33,
                    'band_structure_without_SOC':'7e31c366-f5cb-466b-a1c7-1e29157bf529',
                    'fermi_without_SOC':-4.47024535036518,
                    'band_structure_with_SOC':'7eb853cf-a7ed-4efe-b502-f79dc478f531',
                    'fermi_with_SOC':-4.48903648635301,
                    'phonons':'3d814ffb-6964-4894-b4f0-ff3463b7cada',
                    'structure':'2521a92b-adb2-4f3a-aa01-4907b0197010',
                    }
#Ir2Ta2Te8
data_dict['TaIrTe4'] = {'display_formula':'TaIrTe4',
                    'band_gap':11,
                    'space_group':'Pm (6)',#P$m$ (6)
                    'inversion_strength':204 ,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':26,
                    'binding_energy_per_substructure_per_unit_area_rVV10':31,
                    'atoms_per_cell':12,
                    'colors':{'Ir':'dark blue','Ta':'blue','Te':'brown'},
                    'source_db':'ICSD',
                    'db_id':73322,
                    'Z_avg':59.67,
                    'band_structure_without_SOC':'5f31cf39-1435-45a1-ab6f-1a1ff4ccd424',
                    'fermi_without_SOC':-4.35718164171811,
                    'band_structure_with_SOC':'714eba24-027e-4acf-bd16-df50e12332fb',
                    'fermi_with_SOC':-4.31192856572873,
                    'phonons':'727d653f-064d-4fef-af6a-12bc6b2749af',
                    'structure':'6fd851e2-3d4a-4261-b660-54906ff3f1a0',
                    }
#Rh2Ta2Te8
data_dict['RhTaTe4'] = {'display_formula':'RhTaTe4',
                    'band_gap':65,
                    'space_group':'Pm (6)',#P$m$ (6)
                    'inversion_strength':215 ,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':26,
                    'binding_energy_per_substructure_per_unit_area_rVV10':31,
                    'atoms_per_cell':12,
                    'colors':{'Rh':'dark blue','Ta':'blue','Te':'brown'},
                    'source_db':'ICSD',
                    'db_id':656453,
                    'Z_avg':54.33,
                    'band_structure_without_SOC':'d5b324cd-091b-4339-999b-a2ba34aae060',
                    'fermi_without_SOC':-4.43158048410502,
                    'band_structure_with_SOC':'5146a218-06e0-4c11-8f57-9d326329a60c',
                    'fermi_with_SOC':-4.44342049610953,
                    'phonons':'320be9f3-eb05-419a-8c54-686fa4bc0439',
                    'structure':'15e038b7-9b64-4d14-b877-539778583927',
                    }
#Pd4Hg2Se6
data_dict['Pd2HgSe3'] = {'display_formula':'Pd2HgSe3',
                    'band_gap':0,
                    'space_group':r'P<SPAN STYLE="text-decoration:overline">3</SPAN>m1 (164)', #P${\bar{3}m1}$ (164)
                    'inversion_strength': 80 ,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':61,
                    'binding_energy_per_substructure_per_unit_area_rVV10':66,
                    'atoms_per_cell':12,
                    'colors':{'Hg':'grey','Pd':'dark blue', 'Se':'orange'},
                    'source_db':'ICSD',
                    'db_id':259367,
                    'Z_avg':45.67,
                    'band_structure_without_SOC':'be7d9d93-c13e-412e-a23f-205127113477',
                    'fermi_without_SOC':-5.12243406546198,
                    'band_structure_with_SOC':'2414ce9f-f5da-4f96-bbdd-246f4ed1b370',
                    'fermi_with_SOC':-5.12243406546198,
                    'phonons':'70c2da98-1311-43cb-8690-f607fe81bc21',
                    'structure':'8b8967b0-b6a5-4aed-831e-f8e57cb389d6',
                     }
#Pt4Hg2Se6
data_dict['Pt2HgSe3'] = {'display_formula':'Pt2HgSe3',
                    'band_gap': 149,
                    'space_group':r'P<SPAN STYLE="text-decoration:overline">3</SPAN>m1 (164)', #P${\bar{3}m1}$ (164)
                    'inversion_strength': 168,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':60,
                    'binding_energy_per_substructure_per_unit_area_rVV10':63,
                    'atoms_per_cell':12,
                    'gw_inversion_strength':530,
                    'colors':{'Hg':'grey','Pt':'light grey', 'Se':'orange'},
                    'source_db':'ICSD',
                    'db_id':185808,
                    'Z_avg':56.33,
                    'band_structure_without_SOC':'bc63c379-6fee-4a41-8e45-3e6b15dc596b',
                    'fermi_without_SOC':-4.96961817861078,
                    'band_structure_with_SOC':'a03103b2-6253-42fd-87ae-cdcf7ab2340e',
                    'fermi_with_SOC':-5.012,
                    'phonons':None,
                    'structure':'f7f8c62a-62ed-448e-95cf-7015dc596b0c',
                    }
#In2S4Zn
data_dict['In2ZnS4'] = {'display_formula':'In2ZnS4',
                    'band_gap': 0,
                    'space_group':'P3m1 (156)',#P${3m1}$ (156)
                    'inversion_strength': 191,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':36,
                    'binding_energy_per_substructure_per_unit_area_rVV10':39,
                    'atoms_per_cell':7,
                    'colors':{'In':'purple','Zn':'blue','S':'yellow'},
                    'source_db':'ICSD',
                    'db_id': 44637,
                    'Z_avg':27.43,
                    'band_structure_without_SOC':'047b475a-f899-4cd3-b399-616d4af8c9b1',
                    'fermi_without_SOC':-5.54997365165138,
                    'band_structure_with_SOC':'42d57f09-7ed9-4a8c-bcc4-8f2a1f5918cc',
                    'fermi_with_SOC':-5.29572185254661,
                    'phonons':'747a49b2-550a-47cb-ab3c-936e20b311f3',
                    'structure':'4ee771e7-4441-436f-ab30-9eb6ab353bd0',
                    }
#Cu4Te6Ti2
data_dict['TiCu2Te3'] = {'display_formula':'TiCu2Te3',
                    'band_gap': 8,
                    'space_group':r'C2/m (2)', # C${2/m}$ (2)
                    'inversion_strength': 21,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':44,
                    'binding_energy_per_substructure_per_unit_area_rVV10':44,
                    'atoms_per_cell':12,
                    'colors':{'Ti':'grey','Cu and Te':'brown'},
                    'source_db':'ICSD',
                    'db_id':402631,
                    'Z_avg':39.33,
                    'band_structure_without_SOC':'700232f5-e8d4-47c7-9662-838df8a81a12',
                    'fermi_without_SOC':-4.59594884048797,
                    'band_structure_with_SOC':'9c2cab2f-6112-4ed4-8bdb-b5081bd7c8bd',
                    'fermi_with_SOC':-4.44986888570522,
                    'phonons':'6d03714f-fb1d-46a2-8b32-be3458592e44',
                    'structure':'1ba50b37-8d9b-455c-82fa-e14355cc510b',
                    } 
#Te4W2
data_dict['WTe2'] = {'display_formula':'WTe2',
                    'band_gap':9,
                    'strain_gap_only':2,
                    'space_group':r'P2<sub>1</sub>/m (11)',#' P2$_{1}/m$ (11)'
                    'inversion_strength': 972,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':30,
                    'binding_energy_per_substructure_per_unit_area_rVV10':27,
                    'atoms_per_cell':6,
                    'colors':{'W':'blue','Te':'brown'},
                    'source_db':'COD',
                    'db_id': 2310355,
                    'Z_avg':59.33,
                    'band_structure_without_SOC':'730aee20-ce14-4ad6-8915-2117e30523f8',
                    'fermi_without_SOC':-4.43039231444765,
                    'band_structure_with_SOC':'a92de468-043a-4656-834d-117ce875b8e2',
                    'fermi_with_SOC':-4.31416846498267,
                    'phonons':'141ac792-4f7a-4305-b192-4734731d8aef',
                    'structure':'8afabafa-4254-4c7b-a693-8bd0db3a929f',
                    }
#Mo2Te4
data_dict['MoTe2'] = {'display_formula':'MoTe2',
                    'band_gap': 26,
                    'strain_gap_only':3,
                    'space_group':r'P2<sub>1</sub>/m (11)',#' P2$_{1}/m$ (11)
                    'inversion_strength': 408,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':25,
                    'binding_energy_per_substructure_per_unit_area_rVV10':30,
                    'atoms_per_cell':6,
                    'colors':{'Mo':'light blue','Te':'brown'},
                    'source_db':'COD',
                    'db_id':2310356,
                    'Z_avg':48.66,
                    'band_structure_without_SOC':'07c04a5a-3d44-408e-bdf4-65b227473182',
                    'fermi_without_SOC':-4.54128062290808,
                    'band_structure_with_SOC':'27900650-713c-4187-b636-c9d3bddea4a7',
                    'fermi_with_SOC': -4.2809720861697,
                    'phonons':'d9567945-0795-4778-a069-dee66ef244ed',
                    'structure':'8de3a9ee-4de9-4835-80d0-2c4b386698d1',
                    }
#Br2Zr2
data_dict['ZrBr'] = {'display_formula':'ZrBr',
                    'band_gap': 29,
                    'space_group':r'P2<sub>1</sub>/m (11)',#' P2$_{1}/m$ (11)
                    'inversion_strength': 45,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':16,
                    'binding_energy_per_substructure_per_unit_area_rVV10':22,
                    'atoms_per_cell':4,
                    'strain':1,
                    'colors':{'Br':'red','Zr':'light blue'},
                    'source_db':'COD',
                    'db_id':4343762,
                    'Z_avg':37.5,
                    'band_structure_without_SOC':'3bc96bfd-4ea9-4d77-bbeb-232ba6301a20',
                    'fermi_without_SOC':-3.58916775796,
                    'band_structure_with_SOC':'3d79beba-f901-4d4d-9132-cac9bca9ea4e',
                    'fermi_with_SOC':-3.44406198088404,
                    'phonons':'04cdbfb7-f9ec-474e-a720-c70da72a60f4',
                    'structure':'13535e66-9d02-41bb-b8c5-ea16f582fb8f',
                    }
#Cl2Zr2
data_dict['ZrCl'] = {'display_formula':'ZrCl',
                    'band_gap': 39,
                    'space_group':r'P2<sub>1</sub>/m (11)',#' P2$_{1}/m$ (11)
                    'inversion_strength': 60,
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':15,
                    'binding_energy_per_substructure_per_unit_area_rVV10':22,
                    'atoms_per_cell':4,
                    'strain':3,
                    'colors':{'Cl':'green','Zr':'light blue'},
                    'source_db':'ICSD',
                    'db_id':20148,
                    'Z_avg':28.5,
                    'band_structure_without_SOC':'9d65d6f6-7af7-41b1-866d-8a662ea8834a',
                    'fermi_without_SOC':-3.88320878178305,
                    'band_structure_with_SOC':'7acb2559-981f-4dbc-b4df-2171a8d9993d',
                    'fermi_with_SOC':-3.65375703599694,
                    'phonons': 'a3a0bfd8-fd5a-441d-8f89-b69ae3377a39',
                    'structure':'581c62fb-e150-4289-a626-29801db20f34',
                     }

for k,v in data_dict.items():
    data_dict[k]['bands_without_SOC_y_max'] = 2
    data_dict[k]['bands_without_SOC_y_min'] = -2
    data_dict[k]['bands_with_SOC_y_max'] = 2
    data_dict[k]['bands_with_SOC_y_min'] = -2

observables_dict = {
                    #'abundance':
                    #{'units':"%",
                    # 'plot_label':"Abundance on the Earth",
                    # 'description':"Abundance on the Earth of the rarest of the elements present in the compound",
                    #},
                    'display_formula':
                    {'units':"",
                     'label':"Formula",
                     'description':"Chemical formula",
                     'order':1,
                     'column_group':'2D materials',
                     'default_value':'N/A',
                    },
                    'binding_energy_per_substructure_per_unit_area_rVV10':
                    {'units':"meV / &Aring;<sup>2</sup>",
                     'label':"E<sub>b</sub> (rVV10)",
                     'description':"Binding energy of the bulk 3D, per 2D layer and per unit area,"
                     "obtained with vdW-rVV10 functional",
                     'order':6,
                     'column_group':'E<sub>b</sub>',
                     'default_value':'N/A',
                    },
                    'binding_energy_per_substructure_per_unit_area_DF2-C09':
                    {'units':"meV / &Aring;<sup>2</sup>",
                     'label':"E<sub>b</sub> (DF2-C09)",
                     'description':"Binding energy of the bulk 3D, per 2D layer and per unit area,"
                     "obtained with vdW-DF2-C09 functional",
                     'order':5,
                     'column_group':'E<sub>b</sub>',
                     'default_value':'N/A',
                    },
                    'band_gap':
                    {'units':"meV",
                     'label': 'Band gap (DFT-PBE)',
                     'description':'Electronic band gap of the 2D monolayer, obtained with DFT and the PBE functional with spin-orbit coupling',
                      'order':3,
                     'column_group':'2D materials',
                     'default_value':'N/A',
                    },
                    'inversion_strength':
                    {'units':"meV",
                     'label': 'Inversion strength (DFT-PBE)',
                     'description':'Inversion strength of the 2D monolayer, obtained with DFT and the PBE functional with spin-orbit coupling',
                     'order':4,
                     'column_group':'2D materials',
                     'default_value':'N/A',
                    },
                    'space_group':
                    {'units':"",
                     'label': 'Space group',
                     'description':'Space group of the crystal structure',
                     'order':2,
                     'column_group':'2D materials',
                     'default_value':'N/A',
                    },
                    'source_db':
                    {'units':"",
                     'label':"Source DB",
                     'description':"Database for the 3D parent material",
                     'order':7,
                     'column_group':'3D parent',
                     'default_value':'N/A',
                    },
                    'db_id':
                    {'units':"",
                     'label':"DB ID",
                     'description':"Chemical formula",
                     'order':8,
                     'column_group':'3D parent',
                     'default_value':'N/A',
                    },
                    }

compounds_dict =  { "compounds": {
        "Bi2": {
        "n_species": 1,
        "species": [
        {
        "n_atoms": 1,
        "element": "Bi"
        }],
        },
        "AsCuLi2": {
        "n_species": 3,
        "species": [
        {
          "n_atoms": 1,
          "element": "As"
        },
                {
          "n_atoms": 1,
          "element": "Cu"
        },
                {
          "n_atoms": 2,
          "element": "Li"
        }],
        },
        "I2N2Ti2": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 2,
          "element": "I"
        },
        {
          "n_atoms": 2,
          "element": "N"
        },
                {
          "n_atoms": 2,
          "element": "Ti"
        }],
        },
        "Ir2Nb2Te8": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 2,
          "element": "Ir"
        },
        {
          "n_atoms": 2,
          "element": "Nb"
        },
        {
          "n_atoms": 8,
          "element": "Te"
        }],
        },
        "Ir2Ta2Te8": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 2,
          "element": "Ir"
        },
        {
          "n_atoms": 2,
          "element": "Ta"
        },
        {
          "n_atoms": 8,
          "element": "Te"
        }],
        },
        "Rh2Ta2Te8": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 2,
          "element": "Rh"
        },
        {
          "n_atoms": 2,
          "element": "Ta"
        },
        {
          "n_atoms": 8,
          "element": "Te"
        }],
        },
        "Pd4Hg2Se6": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 4,
          "element": "Pd"
        },
        {
          "n_atoms": 2,
          "element": "Hg"
        },
        {
          "n_atoms": 6,
          "element": "Se"
        }],
        },
        "Pt4Hg2Se6": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 4,
          "element": "Pt"
        },
        {
          "n_atoms": 2,
          "element": "Hg"
        },
        {
          "n_atoms": 6,
          "element": "Se"
        }],
        },
        "In2S4Zn": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 2,
          "element": "In"
        },
        {
          "n_atoms": 4,
          "element": "S"
        },
        {
          "n_atoms": 1,
          "element": "Zn"
        }],
        },
        "Cu4Te6Ti2": {
        "n_species": 3,
         "species": [
        {
          "n_atoms": 4,
          "element": "Cu"
        },
        {
          "n_atoms": 6,
          "element": "Te"
        },
        {
          "n_atoms": 2,
          "element": "Ti"
        }],
        },
        "Te4W2": {
        "n_species": 2,
         "species": [
        {
          "n_atoms": 2,
          "element": "Mo"
        },
        {
          "n_atoms": 4,
          "element": "Te"
        }],
        },
        "Mo2Te4": {
        "n_species": 2,
         "species": [
        {
          "n_atoms": 2,
          "element": "Mo"
        },
        {
          "n_atoms": 4,
          "element": "Te"
        }],
        },
        "Br2Zr2": {
        "n_species": 2,
         "species": [
        {
          "n_atoms": 2,
          "element": "Br"
        },
        {
          "n_atoms": 2,
          "element": "Zr"
        }],
        },
        "Cl2Zr2": {
        "n_species": 2,
         "species": [
        {
          "n_atoms": 2,
          "element": "Cl"
        },
        {
          "n_atoms": 2,
          "element": "Zr"
        }],
        },
      }}


plot_dict = {'x_field':'Z_avg',
             'y_field':'band_gap',
             'x_labels':'Average atomic number <SPAN STYLE="text-decoration:overline">Z</SPAN>',
             'y_labels':'Band gap E<sub>g</sub>',
             'x_units':'',
             'y_units':'meV',            
            }

grid_dict = {}
for k,v in observables_dict.items():
    grid_dict[k] = v['order']

caption_dict = {
                'band_structure_without_SOC':
                'Energy bands with scalar-relativistic pseudopotentials in a representative window'
                'around the Fermi energy and along a high-symmetry path.',
                'band_structure_with_SOC':
                'Energy bands with fully-relativistic pseudopotentials in a representative window'
                'around the Fermi energy and along a high-symmetry path.',
                'phonons':
                'Phonon frequencies along a high-symmetry path.'
                }


index_dict = {}
index_dict['observables'] = observables_dict
index_dict['plot_info'] = plot_dict
#index_dict['grid_info'] = grid_dict
index_dict['caption_info'] = caption_dict

#Compounds dict is not used anymore
#for k,v in compounds_dict.items():
#    index_dict[k] = v

with open('2dtopo_index.json','w') as f:
    json.dump(index_dict,f,indent=3)

exclude_keys = ['ICSD','COD','colors','gw_inversion_strength']
mc_data_dict = {}
for k,v in data_dict.items():
    info = {kk:vv for kk,vv in v.items() if kk not in exclude_keys}
    mc_data_dict[k] = info

with open('2dtopo_data.json','w') as f:
    json.dump(mc_data_dict,f,indent=3)

