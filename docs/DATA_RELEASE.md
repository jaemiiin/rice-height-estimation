# Approved study-data release

The repository owner confirmed all research-data and code publication permissions and requested distribution of the previously withheld dataset. All **214 reviewed files** are retained because they are inputs or reference outputs for the primary study or the documented supplementary comparisons. No synthetic records or missing results were created.

## Files and hosting

| Material | Files | Distribution |
|---|---:|---|
| Original RGB images | 92 | Complete Release ZIP; excluded from Git history |
| Metadata, labels and coordinates | 9 | Git and complete Release ZIP |
| Main/spatial/ROI feature tables | 87 | Git and complete Release ZIP |
| Reference predictions and result tables | 26 | Git and complete Release ZIP |
| Total | 214 | All files in the complete Release ZIP |

The manifest `provenance/data_files.json` records every original relative path, byte size, SHA-256, hosting method and experiment scope. There are 110 files for the primary/main comparisons, 80 for additional spatial sensitivity and 24 for optional ROI comparisons. The 37-candidate primary implementation remains the paper's main analysis; the 34/35-candidate ROI controls and six-feature post hoc analyses do not replace it.

- [Versioned data release](https://github.com/jaemiiin/rice-height-estimation/releases/tag/data-v1.0.0).
- [Complete study-data ZIP](https://github.com/jaemiiin/rice-height-estimation/releases/download/data-v1.0.0/rice-height-study-data-v1.0.0.zip).
- [Archive checksum](https://github.com/jaemiiin/rice-height-estimation/releases/download/data-v1.0.0/SHA256SUMS.txt).
- [Downloadable 214-file manifest](https://github.com/jaemiiin/rice-height-estimation/releases/download/data-v1.0.0/data_files.json).

Archive size: **665,284,341 bytes**. Archive SHA-256:

```text
432ee5016d63426463e949f88b91a0aff90d85b16b3b2044b8e9530396475c43
```

GitHub's automatic Source code ZIP contains the Git files and excludes the original RGBs. Use the specifically named study-data asset for all images. The complete data ZIP contains paths starting with `data/` and `results/reference/`, without an extra enclosing folder.

## Download and verification

After cloning the repository:

```text
python tools/download_data.py
python tools/verify_dataset.py --include-raw
python src/verify_integrity.py --scope all
```

The downloader uses Python's standard library, checks the pinned archive digest and every file digest, preserves original bytes, and refuses to replace a differing existing file. A matching dataset already installed is verified without another download. Use `--archive path/to/rice-height-study-data-v1.0.0.zip` for an offline ZIP or `--destination path/to/project-root` for a different root. Downloads are cached under ignored `.local/downloads/` by default.

The Git checkout alone contains the features and references required for fresh main model fitting. Download the ZIP when reconstructing features from pixels or when obtaining the entire data collection separately.

## Reproducing the results

Use the original two environments listed in the README. With the analysis environment active:

```text
python experiments/reproduce_main.py --out results/runs/main-data-release-01
python experiments/verify_results.py --results results/runs/main-data-release-01/results
```

With the separate pixel environment active:

```text
python experiments/extract_features.py --out results/runs/pixels-data-release-01
```

Every output directory must be new. To explicitly feed re-extracted matrices into modeling, follow the `fresh-data/processed` example in the README. The main model remains continuous ExG weighting, adaptive six-strip selection, 37 candidates, inner image-mean Lasso one-SE, backward BIC, training-strip OLS and outer nine-region LORO. Dates are metadata, not image-model predictors. The 33 shared region-date height values remain shared across their original 92 image records.

Expected primary metrics: RMSE **6.67 cm**, MAE **5.06 cm**, R² **0.9000**. The existing precise local result is 6.666608768631186, 5.057594439678164 and 0.9000213960947129, respectively. Recorded reference predictions are comparison targets and are never substituted for fresh fitting.

## Release checks and limitations

The 214 originals were hash-checked before packaging and again against every ZIP member. All 92 image hashes, 552 retained strips, nine regions and 33 shared height groups were verified. Text screening covered the 122 metadata/feature/result files for absolute personal paths, credential patterns, email addresses and personal phone-number formats, with no findings. All 92 images had no EXIF entries, and contact-sheet inspection found no visible identifiable people or personal documents. This is a documented screening scope, not an absolute guarantee about every possible form of identifying information.

The original 92-image pixel reproduction and main/supplementary model validation are described in [VALIDATION.md](VALIDATION.md). The data archive is independently checked before extraction. No numerical research-source function is changed by adding the download and integrity utilities. Additional spatial/ROI pixel construction workflows and all manuscript figure rendering are not newly claimed as implemented. A clean network package installation and execution on other operating systems remain untested.

For this data release, the complete ZIP was extracted into a new verification directory and all 24 main analyses were freshly fitted from those extracted inputs. The 2,208 OOF predictions matched the reference values exactly (maximum absolute difference 0). The primary scores remained RMSE 6.666608768631186 cm, MAE 5.057594439678164 cm and R² 0.9000213960947129. Machine-readable evidence is recorded in `validation/data_release.json` and `validation/data_release_model_reproduction.json`. This release check did not repeat the earlier full 92-image pixel extraction; the distributed raw and feature files were instead proven byte-identical to the fully validated originals.

## Material that remains excluded

No file from the reviewed 214-file study set remains withheld. Installed virtual environments, transient logs, complete local fitting caches and redundant generated runs, preparation snapshots and the historical permission-pending review log remain local because they are unnecessary release inputs or machine-specific records. Original LaTeX and PDF manuscripts are not part of this data release and were not modified.

The source of the imagery and height references is credited to the National Institute of Crop Science, Rural Development Administration. Publication permission is confirmed by the owner. General reuse licenses, the final manuscript DOI and any future dataset DOI must be specified by the rights holders; no Zenodo record or license has been invented.
