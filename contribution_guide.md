# Contribution Guide

A contribution is one data section (e.g. `core`, `supercon`, `mechanical`,
`fermisurf`) of a database version. They live at:

```text
mc3d-data/data/<version>/<section>/   # e.g. mc3d-data/data/pbesol-v1/mechanical/
mc2d-data/data/<version>/<section>/
```

## Required files

Each `<section>/` must contain:

| File | Role | Required |
| -- | -- | -- |
| `base.json`       | Generated per-material data, keyed by MCXD id (`mc3d-xxxxx`). Derived data — regenerate, don't hand-edit. | Yes |
| `meta.json` | Versioned frontend schema: the `index-columns` list. Used to render values in the table on the landing page | Yes |
| `citation.json` | A citation json file that will be used to render the numerous styled citations on detail page. It should contain all relevant data and paper citations | Yes |
| `METHODOLOGY.md` | A markdown file explaining the methodology of the section in moderate detail to be rendered on https://mc3d.materialscloud.org/contributions/ | Yes |
| `README.md` | Detailed description on how to generate the base json and also the meaning of values in meta/base.json | Yes |
| `description.md`  | A single paragraph markdown file to be rendered on the detail page of a given entry. Should act as a abstract for the data.                            | Yes | 
| `contribution.md` | A markdown file of the relevant publications to be used in the contributions section as a footer. | Yes |
| `scripts/gen.py`  | Scripts required to produce the base.json ephemerally. The usage should be explained in the README.md                                                  | Yes but exceptions |
| `${section}_live_${DATE}.png` | It is often useful after completion/large modification of a section to place a png here so future development can get a historic state of the frontend | Preferred|
| `Other files`  | Small sections, text strings as markdown files. sketches etc.  Are nice to place here aswell. | Preferred |

---
Notes:
- The  meta and base json files are used to populate the mcxd-mongoDB. Thus mistakes / typing errors here will propagate (and may be hard to catch), we suggest you write a verification script to run after population to ensure that expected keys are present, and are the correct datatype and within the correct range.

- The citation.json and METHODOLOGY.MD file is manually copied into the mcxd-frontend AS IS. This is done for performance and to reduce coupling. These are pretty easy to catch if there are issues.

- The other markdown files will be used 'liberally' as a developer guide for the appearance of frontend components.