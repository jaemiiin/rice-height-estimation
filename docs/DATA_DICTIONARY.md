# Data dictionary

## Image and reference metadata

`images.csv` has one row per retained image: `image_id` (the original stem), `region`, ISO `acquisition_date`, `site_date_id`, `shoot_length_cm`, relative raw-image path, `n_strips=6`, and the raw-image SHA-256 hash. `site_date_heights.csv` has one row per shared region-date reference, with its height and number of images. These tables are restructured from the existing retained-strip coordinate/label file. No new height observations were created and no replicate images were assigned independent measurements.

`raw_image_manifest.csv` preserves the original headers `Region`, `파일명`, `relative_path`, and `sha256`. `retained_strip_coordinates.csv` preserves `Region`, `파일명`, `site_date`, zero-based `strip_order`, pixel boundaries `x1`/`x2`, original `width`/`height`, and `shoot_length_cm`. Crops use `image[:, x1:x2]`; the right endpoint is exclusive.

Dates, region identifiers, filenames, and raw hashes are indexing/provenance data. The image-model feature list explicitly excludes them. `site_date` retains the original `YYYYMMDD` string to avoid changing joins.

## Main feature tables

The five tables retain 552 rows and 41 columns in the original order: `Region`, `파일명`, `site_date`, 37 candidates, then `shoot_length_cm`. Continuous, raw and Otsu representations share the recorded adaptive coordinates. Matched equal-width and full-width equal-width variants use the original partition definitions. Every included pixel contributes to the feature mean, including black pixels and zero-assigned ratios.

The authoritative expressions are `src/feature_extraction.py:features`; the authoritative candidate order is `src/common.py:FEATURES`, also recorded in `config.json`. Color intensities and ratios are evaluated using the original types. `complexity`, `mean_R`, `mean_G`, `mean_B`, and `IPCAS` are divided by 255 as in the study. Position descriptors preserve their original centered, absolute-boundary representation. Do not standardize or divide the stored inputs a second time outside the fitting routines.

Exact-zero denominators produce zero. EVIgreen uses integer `D = 14R + 4G - 13B` and returns `5(G-R)/D` where `D != 0`. NGRDI and VARIs have identical definitions; these and other dependencies are part of the original candidate pool. The candidates are not asserted to be 37 independent information sources. NDBGRI is excluded. NExGR is provided separately only for COM/baseline support.

## Additional experiments

`processed/spatial/` contains one table for each of 71 conditions, with 37 candidates and `92 × k` rows. `metadata/spatial/experiment_grid.csv` describes condition IDs, representation, and strip count; the coordinate tables preserve spatial definitions. `results/reference/spatial/` holds the existing OOF and metric records.

`processed/roi34/` and `processed/roi35/` retain the original A/B/C/D input tables. A/B/C use 92 rows and D uses 552 rows. C and D select on the same canonical image means. The 35-candidate variant adds archived crop-local Sobel complexity; it still excludes start/end. These are optional post-study comparisons, not replacements for the primary evaluation.

All data, metadata containing labels, and reference prediction files await redistribution review, regardless of whether an image or a derived table is small enough to commit to Git.
