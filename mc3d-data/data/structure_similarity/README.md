# MC3D Structure Similarity Pipeline

This repository contains Python scripts for computing similarity between crystal structures in the MC3D dataset using SOAP descriptors. The workflow downloads CIF structures, generates SOAP vectors, computes similarity matrices, and prepares the final JSON for downstream analysis or database insertion.

Inspired largely by [dscribes tutorial](https://singroup.github.io/dscribe/latest/tutorials/tutorials.html#similarity-analysis) for general structure comparison;

The structure comparison metric is SOAP, however many others exist, which may be worth measuring for benchmarks.

_Within the documentation its heavily implyed that running full nearest neighbours cosine analysis on many structures inefficient._

Each step of the pipeline can be ran individually in the following order:

```
1. download_structures.py # DownloadsCIF files for all MC3D structures.
2. generate_soap_vector.py # Generates SOAP vectors from CIF structures
3. calculate_similarity.py # Computes nearest neighbors for all structures based on SOAP vectors.
4. prepare_final_json.py # Merges individual similarity JSON files into final structure-based JSON
```

Alternatively the `pipeline.py` offers a simple cli that generates a named final structure json. The mcxd-pipeline cli expects this file to be called 'similarity.json' so be sure to rename the file.
