# Rice plant-height estimation from RGB images

Research code for **“An Interpretable Framework for Rice Plant-Height Estimation from Single Top-View RGB Images Using Continuous ExG Weighting”**, prepared for submission to *Plant Methods*.

The study estimates rice plant height from single top-view RGB images, using continuous excess-green (ExG) weighting, adaptive canopy strips, and interpretable regression. This project preserves the final 37-candidate implementation and its recorded evaluation protocol.

**Public release scope:** research code, environment specifications, documentation, and aggregate validation summaries. **The RGB images, measured height labels, image-level metadata, derived feature tables, and reference prediction files are not distributed in this repository.** The images and height data were provided by the National Institute of Crop Science, Rural Development Administration; redistribution permission has not been established. Full reproduction requires a separately authorized copy of these data, for which no public download is currently provided. The authors' local working folder retains the complete data, but a Git clone does not include them. No reuse license has been assigned. See [Data and code availability](#data-and-code-availability) and [the public release scope](docs/PUBLIC_RELEASE.md).

## Method overview

1. Decode the original RGB images. Compute `clip(2G - R - B, 0, 255)`, divide by 255, and apply the continuous weights to RGB. Preserve the original float32 calculation and conversion to uint8.
2. Smooth the column-wise ExG profile with a Gaussian filter (`sigma=20`). Detect boundaries with the archived prominence and edge rules. Retain three usable strips at each end of the candidate ordering.
3. Extract 37 candidates: 34 color-related descriptors plus `start`, `end`, and `complexity`. NDBGRI is excluded. Pixel expressions, exact-zero denominator handling, and fixed scaling are retained in `src/feature_extraction.py`.
4. Within each outer regional training set, use image means of the six strips for Lasso screening. Tune 200 penalties with inner regional LORO and the one-standard-error rule, then apply backward BIC.
5. Fit OLS to the training strips using the selected features. Average the six predictions for each held-out image.
6. Pool the predictions from the nine outer held-out regions. Each image has equal weight in the primary evaluation. A separate sensitivity gives each shared region-date reference equal total weight.

The primary model selects features inside each outer fold. Its selected subsets contain 3–10 predictors. The six repeatedly selected features (`start`, `end`, `complexity`, `mean_R`, `MGRVI`, `COM`) define a **post hoc exploratory reference configuration**. Its refitted performance and full-data equation are separate from the primary held-out evaluation.

Acquisition date and time are metadata, not predictors in the image models. The date-only diagnostic is explicitly separate. Predictor scaling, response transformations where applicable, feature selection, and tuning use training observations only.

## Repository structure

```text
rice-height-estimation/
  README.md
  requirements-analysis.txt       # Python 3.12.14 model environment
  requirements-pixels.txt         # Python 3.9.18 image environment
  requirements-figures.txt        # Optional figure dependencies
  config.json                    # Recorded, fixed study settings
  config/                        # Environment and optional ROI configurations
  data/
    raw/<Region>/*.jpg            # 92 unchanged images; permission pending
    processed/                   # Five main feature matrices and fixed RGB baseline
      spatial/                   # 71 spatial-condition matrices
      roi34/, roi35/             # Optional controlled-comparison inputs
    metadata/                    # Images, 33 references, strip coordinates, hashes
  src/                           # Preserved numerical implementation and path adapters
  experiments/                   # Supported command-line entry points
  tools/                         # Dataset, integrity, and release checks
  results/
    reference/                   # Archived numerical targets; permission pending
    runs/                        # New outputs; ignored by Git
  validation/                    # Validation summaries for this preparation
  provenance/                    # Relative source aliases, hashes, file inventories
  docs/                          # Code map, data dictionary, validation and release notes
```

No original manuscript, PDF, old environment, or historical working directory is needed to execute the study. `.venv-*` folders, if present locally, are validation environments and are excluded from release.

## Dataset description

The following describes the retained research dataset and the files expected by the code. These data files are **not included in the public Git repository**; only directory README files are supplied.

The retained dataset contains **92 images from nine regions**, six strips per image (**552 strips**), and **33 shared region-date height reference values**. The image dimensions and original file identities are preserved. Multiple images from a region-date group share the same height reference; 92 images are not 92 independent field measurements.

- `data/metadata/images.csv`: 92 image-to-region/date/reference/file correspondences.
- `data/metadata/site_date_heights.csv`: the 33 unique shared height references in centimeters and image counts. This is an exact restructuring of existing study labels, not a new measurement dataset.
- `data/metadata/raw_image_manifest.csv`: original relative filenames and SHA-256 hashes.
- `data/metadata/retained_strip_coordinates.csv`: original six intervals, dimensions, identifiers, and labels.
- `data/processed/features_{continuous,raw,otsu,matched,full}.csv`: 552 rows each, with 37 features, three identifiers, and `shoot_length_cm` (41 columns).
- `data/processed/fixed_baseline_NExGR_continuous.csv`: the additional NExGR component used by the fixed RGB-index baseline; it is not a 38th selection candidate.

The original feature-table identifier `파일명` means “filename/image ID.” It is retained to preserve the existing data and calculations. New correspondence tables use English headers. Region-date IDs and dates are bookkeeping keys and never enter the 37-feature input matrix. See [the data dictionary](docs/DATA_DICTIONARY.md).

## Installation

Use two separate environments. Do not merge them without additional validation.

| Environment | Python | NumPy | pandas | SciPy | Other core library |
|---|---|---|---|---|---|
| Model analysis | 3.12.14 | 2.3.5 | 3.0.1 | 1.18.1 | scikit-learn 1.9.1 |
| Pixel extraction | 3.9.18 | 1.26.4 | 2.1.4 | 1.13.1 | OpenCV 4.11.0 (`4.11.0.86` distribution) |

From the project root, create an environment using the specified Python interpreter. For example, with Python 3.12.14 selected:

```text
python -m venv .venv-analysis
```

Activate it (`.venv-analysis\Scripts\Activate.ps1` in PowerShell, or `source .venv-analysis/bin/activate` on POSIX), then:

```text
python -m pip install -r requirements-analysis.txt
python src/runtime_check.py
```

Create `.venv-pixels` with Python 3.9.18, activate that environment, and install:

```text
python -m pip install -r requirements-pixels.txt
```

Optional recurrence plotting uses the analysis environment plus:

```text
python -m pip install -r requirements-figures.txt
```

The entry points check the recorded versions. The recorded MLP seed is 7; it uses eight tanh hidden units and 2,500 fixed epochs. Numerical thread counts are set to one. Other study fitting procedures are deterministic. Different BLAS implementations or operating systems can still affect final floating-point digits; OOF comparison tolerance is an absolute `1e-8`.

## Usage

The code-only checkout supports the following checks without study data or scientific libraries (Python 3.9 or later):

```text
python src/verify_integrity.py --scope public
python experiments/reproduce_main.py --help
python experiments/extract_features.py --help
```

**All data validation, feature extraction, plotting and model reproduction commands below require the authorized data and reference files described above. They cannot complete from a public clone alone.** Do not substitute fabricated inputs for the original dataset. Once an authorized data package is available, retain the documented layout or supply `--data-root`, `--raw-root` and `--reference-root` as appropriate.

The examples below are run from the project root. Script and default input locations are resolved relative to the project, not a user's home folder. Scripts can also be called by their full path from another working directory. Each `--out` is relative to the caller's working directory and must be a **new directory**.

Check the labels and all 92 raw-image hashes without scientific packages:

```text
python tools/verify_dataset.py --include-raw
```

In the analysis environment, check the supplied feature matrices and stored reference predictions:

```text
python experiments/verify_results.py
python experiments/verify_results.py --spatial
```

In the pixel environment, reconstruct all five main feature matrices from the 92 original images:

```text
python experiments/extract_features.py --out results/runs/pixels-01
```

This checks original image hashes, re-detected coordinates, and every feature against the supplied tables. For a quick **sample-only** check:

```text
python experiments/extract_features.py --verify-only --limit 1 --out results/runs/pixel-sample-01
```

To explicitly feed newly extracted matrices into modeling, create a new data bundle. In the pixel environment:

```text
python experiments/extract_features.py --out results/runs/fresh-data/processed
python -c "import shutil; shutil.copytree('data/metadata', 'results/runs/fresh-data/metadata')"
```

Then switch to the analysis environment and run:

```text
python experiments/reproduce_main.py --data-root results/runs/fresh-data --out results/runs/main-from-pixels
```

The metadata copy preserves the original labels and coordinates. Extraction never replaces the supplied feature tables. All output locations in these examples must be unused.

An externally downloaded image collection can be provided with `--raw-root path/to/rgb-collection`, using the same `<Region>/<filename>.jpg` layout. `--data-root` can point to an externally unpacked directory containing `processed/`, `metadata/`, and optionally `raw/`. It does not change feature definitions or the evaluation protocol.

## Reproducing experiments

### Main paper analyses

In the analysis environment:

```text
python experiments/reproduce_main.py --out results/runs/main-01
python experiments/verify_results.py --results results/runs/main-01/results
```

This performs fresh fitting for the primary evaluation; raw/Otsu/continuous comparisons; adaptive/matched/full-width partition comparisons; image- and strip-level Ridge; image OLS with the same selected features; the recorded image baselines; and exploratory recurrence/reference/ablation analyses. It also recomputes evaluation weighting, the date-only diagnostic, and archived coordinate summaries. Existing model caches and predictions are not copied to replace fitting.

The fixed-six reference models and ablations are tagged `reference_*` or `ablation_*`. Their feature definition is post hoc; their scores must not be presented as independent validation of selecting those six features.

### Additional spatial sensitivity

```text
python experiments/reproduce_spatial.py --condition edge2__continuous --out results/runs/spatial-sample-01
python experiments/reproduce_spatial.py --condition all --out results/runs/spatial-all-01
```

There are 71 representation/selection conditions covering 29 spatial settings. This entry point refits the supplied spatial feature matrices and compares their OOF predictions. It does not reconstruct the historical manual QC process, bootstrap reporting, or raw-pixel extraction for all additional geometries.

### Optional full-image / selected-ROI comparisons

These subsequent controlled experiments are **separate from the current 37-candidate primary evaluation**:

```text
python experiments/reproduce_roi.py --variant 34 --out results/runs/roi34-01
python experiments/reproduce_roi.py --variant 35 --out results/runs/roi35-01
```

Variant 34 uses color candidates; variant 35 adds complexity. Both exclude position candidates for the controlled comparison. A/B/C/D denote full-image features, selected-ROI features, equal strip-mean features, and strip-level fitting. The two comparison schemes use common or independent training-fold feature selection. These runners start from the archived, validated feature tables; their extra pixel-extraction workflows are not included as new extraction capabilities.

### Recurrence figure

```text
python experiments/make_figure7.py --out results/runs/figure7-01
```

This renders the archived 37-feature recurrence figure. This project is not a manuscript/PDF typesetting project and does not automatically redraw every manuscript figure.

## Expected outputs

The primary reported values are RMSE **6.67 cm**, MAE **5.06 cm**, and R² **0.9000**. They are verification targets, not values used to alter fitting.

| Analysis | R² | RMSE (cm) | MAE (cm) |
|---|---:|---:|---:|
| Primary fold-specific strip OLS | 0.9000 | 6.67 | 5.06 |
| Same-selected-feature image OLS | 0.8702 | 7.59 | 5.87 |
| All-37 strip Ridge, continuous ExG | 0.9037 | 6.54 | 4.94 |
| Final image Elastic Net | 0.8834 | 7.20 | 5.53 |
| All-37 image Ridge, continuous ExG | 0.8736 | 7.50 | 5.66 |

The main run writes:

- `verification.json`: 24 analyses, 2,208 OOF predictions, table and manuscript-score comparisons.
- `results/metrics.csv` and `results/predictions.csv`: analysis-labelled numerical results.
- `runs/<case>/`: fold selections, inner curves, strip/OOF predictions, scalers, and model coefficients.
- `validation/elastic_net_fit_diagnostics.csv`: 441 convergence checks. The fixed limit is 100,000; a nonconverged fit causes failure.
- `results/partition_boundary_summary.csv` and `partition_coverage_summary.csv`: the archived coordinate summaries.
- `models/` and `ridge/`: additional fitting and tuning records.

See [validation notes](docs/VALIDATION.md) and `validation/reproduction_summary.json` for the actual execution performed while preparing this project. Do not equate a sample pixel check with re-extraction of the entire dataset.

Preparation on 2026-11-03 completed the full 92-image extraction and fresh model fitting for all 24 main analyses and all 71 additional spatial conditions. The primary result was RMSE 6.666608768631186 cm, MAE 5.057594439678164 cm and R² 0.9000213960947129. The main and spatial OOF predictions matched their archived references exactly in the recorded environments.

## Data and code availability

The public repository distributes code and aggregate validation evidence. It intentionally excludes the original RGB collection, height labels, per-image metadata, features, predictions and full local runs. The complete retained data remain in the authors' local working copy and were used for the validation reported here. No source image or original research file was modified.

Code repository: [jaemiiin/rice-height-estimation](https://github.com/jaemiiin/rice-height-estimation). Publication of the research code was requested by the repository owner; no general reuse license or third-party data permission is implied.

**Availability placeholders:**

- GitHub repository URL: **https://github.com/jaemiiin/rice-height-estimation**.
- Approved data repository URL / DOI: **TO BE ADDED**.
- Manuscript DOI and publication details: **TO BE ADDED when assigned**.
- Code and data licenses: **TO BE DETERMINED after rights confirmation**.

The local presence of data does not establish redistribution rights. `provenance/release_candidates.txt` lists the public code/documentation files. The detailed `provenance/data_permission_pending.csv` is local-only and excluded from Git because it contains original data filenames. Public provenance and integrity records cover released code/documentation only; the complete pre-release inventories are retained under ignored `.local/`. `.gitignore` excludes the data and reference-result directories. Do not remove these exclusions or force-add the files until permission and hosting decisions are recorded. Licenses may differ between code and data.

The raw images total about **620 MiB**. An approved dataset repository with a persistent identifier is a practical distribution option; unpacking the archive into `data/raw/` preserves the runnable layout. Git LFS is another option to assess after approval. GitHub currently warns for regular Git files above 50 MiB and blocks those above 100 MiB; these are per-file limits, not aggregate dataset limits. [GitHub large-file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) and [Git LFS guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage) were checked on 2026-11-03. See [release preparation](docs/RELEASE_CHECKLIST.md) for the measured sizes and remaining decisions.

## Citation

Provisional manuscript identification:

> Na J, Kwon D, Chang J-K, Do Y, Hong S-J, Kim K-M, Choi H. *An Interpretable Framework for Rice Plant-Height Estimation from Single Top-View RGB Images Using Continuous ExG Weighting*. Manuscript prepared for submission to Plant Methods.

Replace this provisional identification with the final accepted citation, year, volume, article number, and DOI when available. Add a code archive DOI and dataset citation only after those records exist. No publication status or DOI is asserted here.
