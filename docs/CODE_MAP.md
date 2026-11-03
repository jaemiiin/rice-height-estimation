# Implementation and execution map

| Stage | Implementation | Supported entry |
|---|---|---|
| RGB decoding, continuous ExG, Otsu | `src/feature_extraction.py` | `experiments/extract_features.py` |
| Adaptive boundary detection | `src/simplified_detector.py`; caller smoothing/candidate selection in `feature_extraction.py` | Same extraction entry |
| 37 candidates and original feature order | `feature_extraction.py`, `common.py` | Same extraction entry |
| Lasso paths and numerical certificates | `lasso_engine.py`, `sparse_engine.py` | Called by `protocol.py` |
| Regional inner selection and backward BIC | `protocol.py`, `sparse_engine.py` | `experiments/reproduce_main.py` |
| Strip OLS and OOF averaging | `protocol.py` | Main entry |
| Same-selected-feature image OLS | `run_core.py:pred_ols` | Main entry |
| Exploratory recurrence, fixed-six reference and ablation | `run_core.py` | Main entry; separate result labels |
| Raw/Otsu/partition comparisons | `run_remaining.py` | Main entry |
| Image/strip Ridge | `run_ridge.py` | Main entry |
| Elastic Net, PCR, kNN, MLP, mean/RGB baselines | `run_baselines.py`, `image_ml_baseline_analysis.py` | Main entry |
| Date-only diagnostic and result collection | `collect_results.py` | Main entry |
| Existing coordinate summary exporter | `geometry_summary.py` | Main entry |
| 71 spatial conditions | `run_spatial.py` | `experiments/reproduce_spatial.py` |
| Optional ROI controls | `roi34_models.py`, `roi35_models.py` | `experiments/reproduce_roi.py` |
| Feature-recurrence figure | `make_figure7.py` | `experiments/make_figure7.py` |
| Input/result validation | `verify_results.py`, `verify_spatial_records.py`, `tools/verify_dataset.py` | See README |

The final numerical engines are retained. Changes in the public preparation concern project-relative locations, command-line entry points, portable data/reference roots, and documentation. `paths.py` is the only default input-location definition. `RICE_REPRO_OUTPUT` points each run at a fresh output folder. The supported entry points refuse existing output directories; call them rather than invoking intermediate stages out of order.

`config.json` records the fixed implementation. It is not a new hyperparameter-search interface, and editing it does not automatically alter the numerical functions. The original functions and candidate order are the authority for reproducing this study.

The coordinate-summary exporter was recovered from an existing archived implementation. Its arithmetic was preserved; it was not inferred from the expected numerical results. Source aliases, original hashes and destination files are listed in `provenance/copied_files.json`. No absolute research-machine locations are included.
