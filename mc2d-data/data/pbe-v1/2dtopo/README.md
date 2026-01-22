# 2D topological insulators

This folder consists of the raw and formatted data for migrating the [2dtopo data](https://github.com/materialscloud-org/discover-2dtopo-data) section inside of MC2D. Most of the information for a particular material is already handled by the core contribution. Therefore we need to add;

- SOC (Spin orbit coupling) information;
- Missing phonons for materials
- HWCC tracking information (used for HWCC plotting)

The tracking information is stored inside a z2pack json file /2dtopo/original_data, this has been reduced into simplified json;

```json
hwcc: {
  "k": [n], // x positions of each point, *note this isnt uniform
  "wcc": [m[n]], // yvalues of each point
  "gaps": [] // the  mid-point maximum wrapped distance at a given x (plotted in red)
}
```

| Info                           | Path                          |
| ------------------------------ | ----------------------------- |
| Original datafiles             | /original_data/hwcc_json/...  |
| Original plots png             | /original_data/hwcc_plots/... |
| New datafiles (webready)       | /data/hwcc_json/              |
| Script: (_visualise old data_) | /old/plot_hwcc.py             |
| Script: (_old data -> new_)    | /scripts/format_hwcc.py       |
| Script: (_visualise new data_) | /scripts/plot_hwcc            |
