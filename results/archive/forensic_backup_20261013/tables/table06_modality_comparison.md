### Table 6: Cross-Modality Benchmark Comparison (B0 through B4)

| Condition ID | Sensory Modalities | Temporal / State Policy | Event Detection Rate | Missed-Train Rate [95% CI] | Premature-Opening Rate [95% CI] |
| --- | --- | --- | --- | --- | --- |
| B0 | Front Vision Only | Stateless 1-frame threshold | 100.0% (27/27) | 0.0% [0.0%, 12.5%] | N/A (no gt latches) |
| B1 | Audio Only | Stateless horn detection | 100.0% (27/27) | 0.0% [0.0%, 12.5%] | 0.0% [0.0%, 12.5%] (never opens) |
| B2 | Dual Vision + Audio | Stateless 3-frame persistence | 100.0% (27/27) | 0.0% [0.0%, 12.5%] | N/A (no gt latches) |
| B3 | Dual Vision Only | Temporal filtering, stateless | 100.0% (27/27) | 0.0% [0.0%, 12.5%] | N/A (no gt latches) |
| B4 | Dual Vision + Audio | Temporal + State Machine | 100.0% (27/27) | 0.0% [0.0%, 12.5%] | 0.0% [0.0%, 12.5%] |
