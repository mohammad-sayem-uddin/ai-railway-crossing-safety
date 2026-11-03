# Researcher adoption checklist (PREPARATION ONLY)

> PREPARATION_ONLY -- NOT AN APPROVAL, NOT A SNAPSHOT, NOT A HASH BINDING. Nothing below has been done for you. Only you can adopt wording, commit, snapshot and
> author governance records.

Git state when this was prepared: HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`, branch `main`, staged 0, modified tracked 19, untracked entries 363.

## Working-tree protocols (unchanged at preparation time)
| File | SHA-256 | Status |
|---|---|---|
| `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` | unchanged |
| `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | `7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c` | unchanged |

## Proposed replacements (proposal hashes are NOT approved or bound hashes)
| Proposal | SHA-256 | Would replace |
|---|---|---|
| `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md` | `23b383b89c57e97852f60e320c8e4feb25d99ac6492e399db281abb126b92a6d` | `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` |
| `docs/generated/phase2/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md` | `8386c2b295166eb01da644251f1eb5f0d584e207d6dac33f0dcd7849ef56168e` | `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` |

## Steps for you (in order)
1. Read both proposals and both unified diffs. Decide: adopt, request revisions, or preserve
   without adopting.
2. If adopting, copy the wording into the protocol files yourself and remove the `PROPOSED` labels.
   This tool never copies anything.
3. Review `git status` before committing: raw media and generated output trees must not be committed
   by accident. Commit the governing set on a branch you choose.
4. Re-run the manifest build against the final tree, then create the off-Desktop snapshot you
   approve.
5. Compute the final protocol hashes from the adopted files. Only then author the GOV-D1 record.
6. After adoption, the working-tree baselines in this tool and the Phase 2 baseline test are
   intentionally out of date; update or retire them.
