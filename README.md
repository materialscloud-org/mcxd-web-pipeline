# Web pipeline for MC3D and MC2D

This repository contains

- `mcxd-web-pipeline` - pipeline (scripts) to start from AiiDA data, and custom json metadata to generate MCXD-specific metadata as raw json files, directly to MongoDB or to S3.
- `mc3d/mc2d-data` - extra metadata and intermediate json files for essential data.
- `mcxd-rest-api` - REST API to serve the MCXD data from MongoDB and the S3.

Overview/context:

```mermaid
flowchart LR
    D[AiiDA profiles] --> A
    H["Raw data e.g. (fermi surface .bxsf)"] --> A
    E[mc3d/mc2d-data] <--> A

    A[mcxd-web-pipeline] --> B[MongoDB]
    A[mcxd-web-pipeline] --> C[S3: mc-discover-mcxd-public]
    B --> G[mcxd-rest-api]
    C --> K[Frontend]
    G --> K
```
