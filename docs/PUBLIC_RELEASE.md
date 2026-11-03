# Public release scope

Repository: [jaemiiin/rice-height-estimation](https://github.com/jaemiiin/rice-height-estimation).

The repository owner requested publication of the research code. This release contains the preserved implementation, separate environment requirements, experiment entry points, English documentation, code provenance, and aggregate validation summaries. No code reuse license has been selected.

## Included

- RGB/ExG preprocessing, adaptive strip detection and the 37-feature implementation.
- Lasso one-SE, backward BIC, strip/image OLS, regional LORO, baselines and supported sensitivity/model comparison code.
- Separate pixel/model requirements and optional plotting requirements.
- Data schemas and layout descriptions, without study rows.
- Aggregate metrics and verification summaries from the completed local reproduction.
- A code-only SHA-256 inventory and relative source provenance.

## Excluded

| Local location | Material withheld | Reason |
|---|---|---|
| `data/raw/` except README | All 92 original RGB images | Rural Development Administration data redistribution permission is unconfirmed |
| `data/metadata/` except README | Heights, image/date/region mappings, coordinates, image hashes and historical pixel reports | Labels and identifying metadata await the same rights review |
| `data/processed/` except README | Main, spatial and ROI feature matrices | Derived data retain study identifiers and labels; permission is unconfirmed |
| `results/reference/` except README | Archived predictions and detailed result tables | These include measured heights, image identities or data-dependent records |
| `results/runs/` | Full local experiment outputs, models and caches | Generated files can carry restricted study records and are not release inputs |
| `provenance/data_permission_pending.csv` | Exact list of the 214 restricted static data/result files | Contains original filenames; the detailed list is retained locally |
| `.local/` | Full pre-release inventories and preparation snapshots | Contains detailed local-only provenance and excluded records |
| `.venv-*/`, caches and logs | Installed runtimes, dependencies and temporary outputs | Machine-specific, unnecessary for source publication, or potentially identifying |

The excluded study files are retained unchanged in the authors' local working folder. The complete file-level exclusion list and reasons remain available there in `provenance/data_permission_pending.csv`. The public inventories intentionally omit original image filenames and image hashes. No original LaTeX manuscript or PDF is distributed.

## Reproduction and availability

The local preparation reproduced the main paper results: RMSE 6.666608768631186 cm, MAE 5.057594439678164 cm and R² 0.9000213960947129. All 92 images were re-extracted, and the 24 main analyses matched the archived OOF predictions exactly. See [VALIDATION.md](VALIDATION.md) for the actual execution scope.

**A public clone alone cannot run the data-dependent experiments.** It lacks the withheld input and reference files. No public data archive or download permission is currently asserted. Once a separately authorized data package exists, use the documented layout and `--data-root`, `--raw-root` or `--reference-root` options. Do not describe the public repository as an unrestricted data release or a complete standalone dataset download.

The standard-library public integrity check and experiment `--help` commands can run without the data. A clean package installation from an external package index and reproduction on another operating system have not been tested.

## Remaining publication decisions

Confirm data redistribution rights with the provider, select an approved data host, decide code/data reuse licenses, and add actual dataset and manuscript DOI records when available. Repository publication does not substitute for those decisions. The code is published at the owner's request; the absence of a reuse license is stated explicitly.
