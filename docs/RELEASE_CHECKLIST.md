# Release maintenance

Data and code publication permission has been confirmed by the repository owner. The current release includes 214 unchanged study-data/result files. Distribution details are in [DATA_RELEASE.md](DATA_RELEASE.md); the historical local-only permission review is superseded by `provenance/data_files.json`.

## Verification commands

```text
python tools/download_data.py
python tools/verify_dataset.py --include-raw
python src/verify_integrity.py --scope public
python src/verify_integrity.py --scope all
python experiments/verify_results.py
python tools/audit_release.py
```

The first four checks use the standard library. Result verification requires the separate recorded analysis environment. The public integrity scope checks Git-tracked files; `all` additionally checks the 92 RGBs downloaded from the Release asset. The inventory does not hash itself.

`.gitattributes` preserves original byte sequences and line endings. Update the static inventory if a tracked file changes. Do not change input tables or numerical methods merely to match a desired score. The six-feature post hoc configuration stays distinct from the primary fold-specific selection.

## Hosting

Raw files total 649,901,769 bytes. The complete ZIP is 665,284,341 bytes and includes all 214 files. The largest original file is 10,771,519 bytes. Individual images could fit GitHub's regular-Git per-file limit, but a Release asset avoids adding hundreds of MiB of immutable imagery to Git history. LFS was considered; this release needs no LFS client or additional hosting account. No Zenodo deposition or DOI was created.

[Regular Git size limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) and [Release limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) were checked on 2026-11-03. Release assets must be under 2 GiB; the current archive complies.

## Remaining decisions

Select explicit reuse licenses with the rights holders and add real manuscript/dataset DOI records if assigned. Do not represent publication approval as an invented general reuse license. Keep installed environments, transient logs, raw ZIP caches, generated fitting caches and private preparation records out of Git.
