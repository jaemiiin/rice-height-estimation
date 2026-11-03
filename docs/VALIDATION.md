# Validation performed on 2026-11-03

The prepared local project reproduced the current 37-candidate paper analysis. Results below are from actual local executions, not inferred from the presence of archived tables. **These executions used data retained locally by the authors. The public code-only checkout does not include that dataset or its reference predictions and cannot reproduce the results until authorized inputs are supplied.**

## Numerical results

| Check | Executed scope | Result |
|---|---|---|
| Image/label integrity | 92 images, 9 regions, 33 shared region-date labels, 552 strips | PASS; all raw SHA-256 hashes match |
| Full raw-pixel extraction | All 92 images, five representations, 37 candidates, fixed NExGR baseline | PASS; all features bitwise equal; all re-detected coordinates exact |
| Pixel-to-model serialization | Six freshly written CSV files read in the separate analysis environment | PASS; every parsed value, identifier, label and column order equals the supplied matrices |
| Main models | 24 analyses; 2,208 freshly fitted OOF image predictions | PASS; maximum absolute prediction difference 0 |
| Additional spatial sensitivity | All 71 conditions; 6,532 freshly fitted OOF image predictions | PASS; maximum absolute prediction difference 0 |
| Optional 34-candidate ROI control | Eight analyses; 736 freshly fitted OOF predictions; six result tables | PASS |
| Optional 35-candidate ROI control | Eight analyses; 736 freshly fitted OOF predictions; six result tables | PASS |
| Elastic Net convergence | 441 fits | All converged; largest observed iteration count 14,756 of 100,000 |
| Figure 7 | PDF and 300-dpi PNG | Rendered; recurrence checked against nine folds |
| Portability | Relocated code/data copy, different working directory, explicit input/reference roots | PASS; stored-result verification with newly extracted matrices |
| Original-source preservation | 236 original files hashed again after preparation | PASS; every original hash unchanged |

The newly fitted primary scores are:

- RMSE: **6.666608768631186 cm** (paper: 6.67 cm).
- MAE: **5.057594439678164 cm** (paper: 5.06 cm).
- R²: **0.9000213960947129** (paper: 0.9000).

Main fitting used the supplied archived matrices. Full pixel extraction ran separately; its newly serialized matrices were subsequently proven exactly equal in the analysis environment. No second full model fitting was necessary after that equality check. The relocated-copy check verified stored results and input routing; it is not described as a second model refit.

The main fit took about 237 seconds and full pixel extraction about 738 seconds on the preparation machine. These are observed run times, not performance guarantees.

## Evaluation and leakage review

The 37 predictor names exclude acquisition date, region, image identifier, response and NDBGRI. The primary implementation retains image-mean Lasso one-SE selection and backward BIC within each outer training set, followed by training-strip OLS and six-strip prediction averaging. BIC uses training-image residuals. The inner solver standardizes each seven-region training subset separately; the held-out region does not enter these transformations or selection.

Actual saved outputs were audited for **360 inner split boundaries** across the primary and four representation/partition comparisons, **45 outer training-only scalers**, and six-strip aggregation of **460 OOF image predictions**. Every inner training set excluded both the outer held-out region and inner validation region. Saved scaler means and scales exactly matched recomputation from the corresponding training strips. Nine-region LORO keeps every shared region-date target group inside a single outer split.

No held-out-region data leakage was found in the inspected primary pipeline. This is a code/output audit, not a guarantee about the historical collection process. The primary evaluation weights images equally despite 33 shared field references. The existing equal-region-date weighting sensitivity is retained separately.

The six-feature reference configuration and associated ablations are defined retrospectively from selection recurrence. Their performance is exploratory and must not replace the primary fold-specific selection result. Date-only prediction is also a separate diagnostic.

## Environments and installation limits

- Pixels: Python 3.9.18, NumPy 1.26.4, pandas 2.1.4, SciPy 1.13.1, OpenCV 4.11.0 (headless distribution version 4.11.0.86).
- Models: Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, SciPy 1.18.1, scikit-learn 1.9.1.
- Figure rendering: model environment plus Matplotlib 3.11.2.
- MLP seed: 7; numerical thread count: one. Existing selection/tie-breaking rules and solver tolerances are preserved.

Two local virtual environments were made using the recorded Python interpreters and copies of their available installed packages. The scientific modules used for model validation resolve inside the new project's ignored environment; no original research-source directory is injected at runtime. Dependency checks identified additional imported packages (`cloudpickle` and `narwhals`), which are now recorded in the analysis requirements.

**A clean installation from a network package index was not tested.** The supplied requirements identify the actual versions used; wheel availability on other operating systems and numerical differences from other BLAS builds remain to be tested. The virtual environments use installed Python runtimes and are local conveniences, not portable or distributable environment archives.

## Evidence and retained outputs

`validation/reproduction_summary.json` gives the concise machine-readable result. Detailed evidence is in:

- `main_reproduction.json`, `pixel_reproduction.json`, `pixel_model_bridge.json`.
- `spatial_reproduction.json`, `roi34_reproduction.json`, `roi35_reproduction.json`.
- `split_audit.json`, `implementation_preservation.json`, `source_preservation.json`.
- `portability.json`, `dependency_origins.json`, `gitignore.json`, `release_scan.json`.

Full newly generated outputs are retained locally under `results/runs/main-validation`, `pixels-validation`, `spatial-validation`, `roi34-validation`, `roi35-validation` and `figure7-final-validation`. They are excluded from ordinary Git staging. Main fitting caches were generated inside the new output directory; archived fitted caches were not used to bypass training.

The original numerical engines for selection, regression and baselines remain byte-identical. Function-level AST comparison records which functions were adapted for paths, environment activation, run orchestration, or the new integrity inventory. The geometry summary uses the existing archived exporter block, with its arithmetic preserved.

## Scope not claimed

The retained inputs needed for the primary 37-feature study are present. No missing primary RGB file, target value or model implementation was found. Separate field notebooks or a signed redistribution permission record were not supplied.

Additional spatial and ROI analyses can be refitted from the included feature matrices. Their separate raw-pixel construction workflows, historical manual QC and additional bootstrap reporting are not exposed as supported reproduction commands here. Archived ROI pixel-validation reports are marked as historical evidence; they are not fresh extraction results from this preparation. Only Figure 7 is packaged as a figure entry point. The manuscript LaTeX and PDFs are outside this project and were not edited.

Redistribution permission, code/data licenses, permanent repository addresses and a final published citation remain unresolved. Pattern-based path/credential screening cannot prove that every possible secret has been found, and unchanged image metadata still requires the same rights review as the original images.
