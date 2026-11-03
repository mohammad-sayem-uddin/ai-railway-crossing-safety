# Preservation and Snapshot Proposal (RD-003) — PROPOSED; nothing committed, staged or copied

> You perform any Git action. This mission did **not** stage, commit, copy, snapshot or move anything. A hash manifest records bytes; **it does not by itself make the project reproducible** (see the limits below).

## 1. What exists
`REPRODUCIBILITY_MANIFEST_20261101_M5A.json` — SHA-256 per governing file (source, tests, configuration, documentation, schemas, scripts, research code, governance/ground-truth/manifest/split metadata, dependency/environment files), each tagged `tracked-clean` / `tracked-modified` / `untracked`, plus the two frozen checkpoints compared against their expected hashes, plus counts and exclusions. Built by `scripts/mission5a_build_preservation_manifest.py` (read-only; refuses to overwrite). Re-verify any time:

```
python scripts/mission5a_build_preservation_manifest.py verify --root . --manifest docs/generated/mission_5a/REPRODUCIBILITY_MANIFEST_20261101_M5A.json
```

## 2. Exclusions (and why)
Media and binaries are **classified by extension and never opened** (`.mov .mp4 .wav .mp3 .pt` except the two frozen checkpoints, images, archives, office files); `data/raw`, `data/processed`, `results`, `experiments`, `outputs`, `models`, `scratch`, `reports`, `research/figures` are generated/output trees counted but not hashed file-by-file (historical outputs are diagnostic only); `.git`, `.venv`, `venv`, caches, `ESC-50-master`, `Unseen_Video`, `.commandcode` are excluded. The exclusion table with file counts is in the manifest.

## 3. Proposed immutable snapshot structure (for you to create)
```
<destination>/train_gate_governing_snapshot_<UTC-date>/
  MANIFEST.json                 # copy of the manifest above
  MANIFEST.sha256               # sha256 of MANIFEST.json, written read-only
  git/                          # `git bundle` of the branch you commit, plus `git rev-parse HEAD`
  files/                        # byte-identical copies of every manifest entry, same relative paths
  protocols/                    # the final bound v9/v7 bytes, again, with their hashes in the file name
  ENVIRONMENT.txt               # python version, `pip freeze`, platform, git version
```
Make the snapshot read-only (`chmod -R a-w`) and store a second copy off the Desktop (the earlier incident record shows a single Desktop copy is a risk). The destination is **yours to approve**; none is assumed.

## 4. Suggested order
1. Adopt or reject the proposed wording (RD-002). 2. Commit the governing set on a branch **you** choose (the working tree has 19 modified tracked files and hundreds of untracked ones; untracked governing code and documents are the main exposure). 3. Re-run the manifest build against the final tree. 4. Create the snapshot per §3. 5. Only then author the D1 envelope with the final hashes.

## 5. Limits — why hashes are not enough
Hashes prove bytes, not behaviour. Not yet verified: that the environment imports (`ultralytics` now has an `__init__.py` but importability was not tested), `requirements.lock` drift, absence of hidden dependence on untracked files, or that a clean clone reproduces results. No claim of reproducibility is made.
