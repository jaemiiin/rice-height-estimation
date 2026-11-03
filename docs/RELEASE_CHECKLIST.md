# Local release preparation

This checklist originally accompanied the local preparation. The repository owner subsequently requested publication of the code. See [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md) for the current scope; data exclusions and unresolved reuse-license decisions remain in effect.

## Rights and availability decisions

- Confirm redistribution permission for the 92 RGB images, the 33 shared height reference values, derived features, and observed/predicted-height tables. The manuscript acknowledgement is not a permission record.
- Confirm code ownership and any contributor or institutional obligations; then select a code license. Select data licenses separately if appropriate. No `LICENSE` has been invented.
- Decide which optional sensitivity and follow-up comparisons belong in the public release. The 37-candidate analysis remains the primary paper reproduction.
- Add the actual repository URL, approved dataset URL/DOI, and accepted manuscript citation only after they exist.
- Record the approved file list. Then deliberately revise the corresponding `.gitignore` exclusions; do not force-add the entire local working folder.

## Data size and hosting

The 92 original images total **649,901,769 bytes (619.79 MiB)**. The largest individual image is **10,771,519 bytes (10.27 MiB)**. These images are individually below GitHub's current regular-Git per-file threshold, but adding hundreds of MiB of binary history is a separate repository-size concern.

An approved scientific data archive can host the image collection and, if needed, its labels/features as one or more archives with persistent identifiers. Retain the existing relative directory structure and SHA-256 manifest so a download can be used with `--raw-root` or `--data-root`. This project contains no automatic downloader and does not invent a hosted URL. Git LFS is an alternative to evaluate for storage/bandwidth and institutional requirements; it has not been enabled.

GitHub warns for files larger than 50 MiB, blocks regular-Git files larger than 100 MiB, and recommends keeping repositories small. Browser uploads have a separate 25 MiB per-file limit. Sources checked on 2026-11-03: [large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github), [Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).

## Local checks before release

```text
python tools/verify_dataset.py --include-raw
python experiments/verify_results.py
python src/verify_integrity.py --scope public
python src/verify_integrity.py --scope all
python tools/audit_release.py
```

Use the analysis environment for the result check. The other checks use the standard library. The public integrity scope covers released code/documentation; `all` additionally requires the locally staged data and the ignored `.local/provenance/data_inventory.json`. Inventory files do not hash themselves. Generated runs, validation environments and transient logs are deliberately outside the static inventory.

`.gitattributes` disables automatic line-ending conversion so Git preserves the exact bytes recorded by the integrity inventory, including archived files with Windows line endings. Updating a tracked file requires updating its inventory hash before another integrity check.

`provenance/release_candidates.txt` lists the code/documentation selected for this release. `provenance/data_permission_pending.csv` is the local-only data-dependent file list and is itself excluded from Git. Public source and prepared-file hashes are recorded in `provenance/copied_files.json`; full inventories containing original filenames remain under ignored `.local/`. No absolute source paths or data filenames are published in the public provenance records.

The path/credential scan is a pattern-based check, not a universal proof that no sensitive information exists. Binary image bytes are retained unchanged; publication approval should cover the originals and their embedded metadata as supplied.
