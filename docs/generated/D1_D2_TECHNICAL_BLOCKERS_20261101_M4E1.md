# D1/D2 Technical Blockers

**Date:** 2026-11-01  
**Status:** Verification only; D1 selected in conversation but not bound in repository; D2 remains conditional.

## D1 blockers

1. Researcher selection is not recorded in `data/manifests/phase12_protocol_decision.json`.
2. Protocol hashes are not bound to a governance envelope.
3. Current source tree still contains v6/v8 references in comparison logic, schema comments, and legacy annotator docstrings. These are historical/reference bindings, not evidence that v8/v6 is active.
4. Worktree v9/v7 documents align with current operational convention and Stage-2.1 workflow.
5. No migration is required for legacy records; they remain invalidated and must remain intact.

## D2 blockers

1. Profile selection is not recorded in a protocol decision envelope.
2. M4 technical definition is supported by existing code but has no formal researcher binding.
3. Approved T4 ground truth does not exist for any event.
4. R04 scope is unresolved for any fused camera evaluation.
5. Official split, manifest, promotion receipt, and EVAL-AUTH are absent.

## D2 conditional conclusion

The exact M4 start/end definitions are technically supported:
- Start: first retained replay step with `is_passage_blocked=True`.
- End: approved `T4_tail_clearance`.
- No blocked step: M5 `never_protected`, excluded from M4 denominator.

The remaining work is governance binding and evidence completion, not an immediate schema repair.

## Researcher action

The researcher should approve the exact M4 contract and then create the validated decision envelope. Mission 4E.1 does not create it.