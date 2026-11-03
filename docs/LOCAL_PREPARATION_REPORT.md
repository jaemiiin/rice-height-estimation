# Local preparation report (historical snapshot)

This report describes the completed local assembly before GitHub publication. The subsequent code-only release and later approved data release are documented in [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md) and [DATA_RELEASE.md](DATA_RELEASE.md). Statements below about permission-pending exclusions describe the earlier local-preparation snapshot, not the current release. References to all 236 source entries and 53 generated files below describe the full local snapshot; its complete inventories are retained under ignored `.local/pre-public-release/`. Current public provenance also includes the approved study data.

This project is an independent local publication staging folder. It contains the retained data, preserved computational methods, executable experiment entries and English documentation needed to reproduce the current primary paper results. No GitHub repository, remote connection, push, external upload or license assignment was performed.

## Source selection

The primary source was the final analysis integration dated **2026-10-22**, which uses 37 candidates and the converged Elastic Net implementation finalized on **2026-10-19**. Earlier 36- or 38-candidate versions and the earlier Elastic Net iteration cap are not the current primary implementation. Subsequent 34/35-candidate full-image/ROI controls are included as optional, separately labelled follow-ups.

The current 2026-11-03 manuscript still specifies the 37-candidate study and the primary 6.67 cm / 5.06 cm / 0.9000 result. A later folder modification date alone was not treated as evidence that an optional analysis replaces the manuscript method.

## Files brought forward

The local snapshot of `provenance/copied_files.json` lists **236 copied or extracted file entries**, with a source-bundle alias, relative source filename, original SHA-256, prepared destination SHA-256 and adaptation description. These include:

- Nineteen final-source Python scripts, the existing geometry-summary block, and two existing optional ROI model scripts.
- Ninety-two original RGB images, unchanged.
- Five main feature matrices, the fixed NExGR baseline, retained coordinates and the raw-image manifest.
- Seventy-one additional spatial matrices and their existing configuration, geometry and result records.
- Optional ROI feature matrices, historical pixel-validation reports and reference outputs.
- Existing environment specifications and archived main result tables.

Source aliases deliberately identify the research bundle without exposing an absolute machine-specific source path. `validation/source_preservation.json` records the post-build checksum verification of the originals.

## Newly written material and adaptations

The local snapshot of `provenance/generated_files.json` lists the original new files. The public version lists released files only. The principal additions are the English README and documentation, English image/reference correspondence tables, project-relative path definitions, six experiment entry scripts, dataset/release checks, environment metadata, validation summaries, Git exclusion rules and release inventories.

Paths are resolved from the project directory or explicit CLI roots. Run outputs are placed in new directories. Machine-specific dependency injection was removed. The separate image and model environments remain separate. Analysis requirements now identify the observed transitive dependencies; optional plotting requirements are separate.

No feature formula, candidate ordering, label, regional split, primary selection rule, evaluation weighting, random seed or fitting target was changed to obtain the expected scores. The full-data six-feature equation and reference analyses retain their exploratory status.

Issues discovered in the source packaging were addressed only in the new project: machine-dependent dependency loading was replaced by environment installation; the existing coordinate-summary exporter was brought back into the main orchestration; and Figure 7's validation metadata was corrected to name the files actually written into the chosen output directory. The original research files were left unchanged. No numerical correction to the primary model was required.

## Validation result

Full 92-image feature reconstruction passed. All primary features and re-detected coordinates were exact. Fresh fitting reproduced 24 main analyses and 71 spatial conditions with zero OOF prediction differences. Both optional ROI model suites also passed. Primary RMSE was 6.666608768631186 cm, MAE 5.057594439678164 cm, and R² 0.9000213960947129. See [the validation report](VALIDATION.md) for evidence, leakage checks and limitations.

## Outstanding items

No primary-study image, target or numerical implementation is missing from this local project. Additional spatial/ROI pixel workflows and all manuscript figures are not claimed as a complete end-to-end reproduction package. A network-based clean installation and execution on another operating system have not been verified.

Before publication, confirm data and code rights, choose appropriate licenses, approve the data-dependent file list, select hosting for approximately 620 MiB of raw imagery, and replace citation/URL placeholders with real records. `.gitignore` excludes the raw images, labels, derived data, reference predictions, local environments and run outputs while these decisions remain pending. `provenance/release_candidates.txt` is a review list, not publication authorization.
