### Table 7: Impact of Temporal Evidence Filtering on Detection Jitter

| Temporal Metric | Raw Independent Frames (B0) | Temporal Filtering (B3) | Full Policy (B4) / Gain |
| --- | --- | --- | --- |
| Mean Detection Continuity | 76.4% | 91.8% | +15.4% continuity gain |
| Chattering Events (Whole Cohort N=23) | 21 events (91.3%) | 17 events (73.9%) | 0 events (100% eliminated in B4) |
| Chattering Events (Observable Tail N=22) | 20 events (90.9%) | 16 events (72.7%) | 0 events (event_005 excluded due to censoring) |
| Mean Warning Confirmation Latency | 0.20s | 0.40s | 0.40s (confirm_frames=2) |
| Premature Openings Caused by Dropouts | Severe chattering in B0/B3 | Partial smoothing in B3 | 0 events (100% eliminated by state machine) |
