# Rice plant-height estimation

Code and data for **An Interpretable Framework for Rice Plant-Height Estimation from Single Top-View RGB Images Using Continuous ExG Weighting**, a manuscript being prepared for submission to *Plant Methods*.

The pipeline applies continuous ExG weighting → six adaptive strips → 37 candidate features → Lasso 1SE → backward BIC → strip-level OLS → the mean of six strip predictions per image.

Nine-region leave-one-region-out validation performs feature selection, standardization, and model fitting within each fold's training regions. Image-based models do not use acquisition date or time as inputs.

Primary manuscript performance:

| R² | RMSE (cm) | MAE (cm) |
|---|---|---|
| 0.9000 | 6.67 | 5.06 |

## Data

The National Institute of Crop Science, Rural Development Administration supplied 92 original RGB images (3840 × 2160 pixels) from nine regions, with measured heights for 33 region–date groups. Images from the same region and date share the same reference plant height.

The [ground-truth table](data/ground_truth.csv) maps filenames to regions, acquisition dates/times, reference heights, dimensions, and image checksums.

Download [rice-height-images.zip](https://github.com/jaemiiin/rice-height-estimation/releases/download/rice-height-dataset/rice-height-images.zip) from the [Rice Height Dataset Release](https://github.com/jaemiiin/rice-height-estimation/releases/tag/rice-height-dataset). Automatic downloading verifies the ZIP and individual image SHA-256 checksums, then installs the 92 JPEGs under `data/images/`. For manual installation, extract the image ZIP into the repository root.

## Installation

Clone the repository and enter its root directory:

```bash
git clone https://github.com/jaemiiin/rice-height-estimation.git
cd rice-height-estimation
```

Install **Python 3.9.18** for image processing and **Python 3.12.14** for analysis. Create separate environments using [requirements-pixels.txt](requirements-pixels.txt) and [requirements.txt](requirements.txt):

```bash
python3.9 -m venv .venv-pixels
.venv-pixels/bin/python -m pip install -r requirements-pixels.txt
python3.12 -m venv .venv-analysis
.venv-analysis/bin/python -m pip install -r requirements.txt
```

On Windows, create them with `py -3.9 -m venv .venv-pixels` and `py -3.12 -m venv .venv-analysis`; replace `bin/python` with `Scripts/python.exe` in installation commands. The code checks the specified Python patch versions and package versions before processing.

## Run

Run commands from the repository root. To download only the original images, use Python 3.9 or later; no third-party packages are required:

```bash
python code/run_all.py --download-only
```

Run the complete workflow, including the primary analysis and comparison experiments (24 analyses):

```bash
.venv-analysis/bin/python code/run_all.py --download --pixels-python .venv-pixels/bin/python --out results/main
```

Windows PowerShell:

```powershell
.venv-analysis/Scripts/python.exe code/run_all.py --download --pixels-python .venv-pixels/Scripts/python.exe --out results/main
```

Use a **new output directory for every complete run**. The following paths are relative to the selected output directory (`results/main` above):

| Output | Contents |
|---|---|
| `inputs/` | Extracted features and strip coordinates |
| `runs/continuous/` | Primary fold selections, fitted models, and predictions |
| `results/metrics.csv` | Performance across all 24 analyses |
| `results/predictions.csv` | Image-level out-of-fold predictions |
| `verification.json` | Calculated metrics and checks against manuscript scores |

The six-feature reference and ablation analyses are post hoc; the date-only analysis is separate from the image-based models.

## Code

Files are located in `code/`:

| File | Role |
|---|---|
| `run_all.py` | Manage downloads, paths, environments, and execution order |
| `step01_preprocessing.py` | Load RGB and construct ExG-weighted, raw, and Otsu RGB representations |
| `step02_strip_detection.py` | Detect adaptive strip boundaries and comparison partitions |
| `step03_feature_extraction.py` | Extract the 37 candidate features per strip |
| `step04_feature_selection.py` | Perform training-fold Lasso 1SE and backward BIC selection |
| `step05_model_fitting.py` | Fit OLS models and average strip predictions by image |
| `step06_evaluation.py` | Calculate overall/regional metrics and verify manuscript scores |
| `step07_comparisons.py` | Run representation, partition, model, reference, and ablation comparisons |

Step 03 calls functions from steps 01 and 02 for each image. Files beginning with `_` provide shared functionality.

## Citation and reuse

Na J, Kwon D, Chang J-K, Do Y, Hong S-J, Kim K-M, Choi H. *An Interpretable Framework for Rice Plant-Height Estimation from Single Top-View RGB Images Using Continuous ExG Weighting*. Manuscript prepared for submission to Plant Methods.

Final publication details will be added when confirmed. A general reuse license has not yet been assigned to the code or data.
