### Table 10: Fault-Injection Resilience and Safety Invariant Verification

| Scenario ID | Failure Perturbation Mode | Events | MTR | POR | Fault Detected | FAULT_FAIL_SAFE Entered | Invariant Violations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B5a | Camera 1 Dropout (Full Event) | 27 | 0.0% | 0.0% | Yes (27/27) | Degraded Operation | 0 |
| B5b | Camera 1 Dropout (Midway 30-70%) | 27 | 0.0% | 0.0% | Yes (27/27) | Degraded Operation | 0 |
| B5c | Camera 1 Flapping (2s on/2s off) | 27 | 0.0% | 0.0% | Yes (27/27) | Degraded Operation | 0 |
| B6a | Camera 2 Dropout (Full Event) | 27 | 0.0% | 0.0% | Yes (27/27) | Held Closed Conservatively | 0 |
| B6b | Both Cameras Fail (Simultaneous) | 27 | 0.0% | 0.0% | Yes (27/27) | Yes (27/27) | 0 |
| B6c | Both Cameras Fail (Sequential) | 27 | 0.0% | 0.0% | Yes (27/27) | Yes (27/27) | 0 |
| B7a | Audio Dropout (Complete Loss) | 27 | 0.0% | 0.0% | Yes (27/27) | Normal Vision Operation | 0 |
| B7b | Dropped Frames (30% Random) | 27 | 0.0% | 0.0% | Compensated | Normal Operation | 0 |
| B7c | False Detection Injection (0.85 conf) | 27 | 0.0% | 0.0% | Conservative | Warning Triggered | 0 |
| B7d | Timestamp Out-of-Order Swaps | 27 | 0.0% | 0.0% | Yes (27/27) | Rejected by Rule 8 | 0 |
| B7e | Stale Timestamps (2s Midway) | 27 | 0.0% | 0.0% | Yes (27/27) | Rejected by Tracker | 0 |
| B7f | Compound Audio Loss + 10% Frame Drop | 27 | 0.0% | 0.0% | Compensated | Normal Operation | 0 |
