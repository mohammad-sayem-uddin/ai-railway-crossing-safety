### Table 9: Primary Safety Endpoints Summary Across Benchmark Conditions

| Condition | Description | Eligible Events | Operational Gate Behavior | Missed-Train Rate (MTR) | Premature-Opening Rate (POR) |
| --- | --- | --- | --- | --- | --- |
| B0 | Vision Only (raw frames) | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B1 | Audio Only (no vision) | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B2 | Vision + Audio (stateless) | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B3 | Temporal Evidence (dual vision) | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B4 | Full Proposed Policy | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B5a | Camera 1 Intermittent Dropout | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B5b | Camera 1 Permanent Dropout | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B5c | Camera 1 Temporal Delay | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B6a | Camera 2 Rear Dropout | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B6b (Original) | Dual Camera Blackout (Flawed IDLE Fail-Safe) | 27 | 0.0s closed (Failed Fail-Safe in IDLE) | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B6b (Corrected) | Dual Camera Blackout (Corrected FAULT_FAIL_SAFE) | 27 | 48.3s mean closed (FAULT_FAIL_SAFE @ 0.4s) | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B6c | Camera Rate Asymmetry | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7a | Audio Loss Robustness | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7b (Original) | Dropped Frames 30% (Flawed Injector: 100% Drop) | 27 | 0.0s closed (100% Injected Drop) | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7b (Corrected) | Dropped Frames 30% (Corrected Deterministic PRNG) | 27 | 45.2s mean closed (PRNG Drop Compensated) | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7c | False Detection Noise | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7d | Timestamp Disorder | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7e | Stale Timestamps | 27 | Normal Safe Operation | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7f (Original) | Compound Audio Loss + 10% Drop (Flawed Injector) | 27 | 0.0s closed (100% Injected Drop) | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
| B7f (Corrected) | Compound Audio Loss + 10% Drop (Corrected PRNG) | 27 | 45.2s mean closed (PRNG Drop Compensated) | Blocked (GT Unapproved) | Blocked (GT Unapproved) |
