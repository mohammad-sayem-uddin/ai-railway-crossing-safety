### Table 1: Multi-Layer Dataset Inventory and Isolation Scheme

| Dataset Layer | Total Samples | Target Classes | Split Composition | Role | Isolation Mechanism |
| --- | --- | --- | --- | --- | --- |
| Layer A: Vision | 3,157 annotated images | front, side, rear | 2,218 train / 467 val / 472 test | YOLOv8n Development | Group-disjoint / Frozen |
| Layer A: Audio | 2,276 audio files (276 horn / 2,000 ESC-50) | train_horn vs ambient | Group-disjoint cross-validation | CompactTrainHornCNN Dev | ESC-50 + Field / Frozen |
| Layer B: Real Events | 27 active events (54 videos, 2,617s) | passage approach/departure | 23 train / 3 no-train / 1 engine | Final Multimodal Evaluation | 100% Unseen / Frozen |
| Layer B: Audio | 54 extracted tracks (16kHz mono) | ambient / train horn | 4,741 windows evaluated | Evaluation Only | Excluded from Training |
