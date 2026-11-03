# B7d/B7e Perturbation Contracts

**Status:** `PROPOSED — NOT APPROVED`; no implementation change made.

## B7d ordering alternatives

1. **Delivery-layer disorder:** preserve arrival order and let collector/Rule 8 reject out-of-order
   observations; tests must observe rejection. Meaning: transport disorder.
2. **Timestamp/data corruption:** mutate timestamps while preserving delivery order; explicit
   monotonicity policy required. Meaning: sensor clock fault.

Current injector swaps frames, but `EventSimulationRunner` sorts them before processing, so the
current perturbation may be erased. Researcher must choose intended fault meaning.

## B7e stale-timestamp alternatives

1. repeated/stuck timestamp;
2. delayed timestamp (content current, timestamp old);
3. stale-frame replay (content and timestamp repeated).

Each requires bounds, source scope, deterministic seed behavior, expected rejection/state behavior,
and separate tests. No option is selected; no stale branch exists in `FailureInjector`.

**Response:** B7d contract __________; B7e contract __________; rationale/decision-maker/date __________.
