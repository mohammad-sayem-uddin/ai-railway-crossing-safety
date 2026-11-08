# Reading copy — CHECKPOINT_IDENTITY_VERIFICATION.md

Derived presentation copy: local links are adapted for this package. Evidence text and historical status retain their original scope. Consult the current executive guide for the final result status. [Byte-identical original](../../../../../originals/docs/generated/master_reaudit/mission37/CHECKPOINT_IDENTITY_VERIFICATION.md). Original SHA-256: `d4ba915d000ec2b5fbc30619da1c79c962af17099a2108304c930baab801f83b`.

# Mission 37 checkpoint identity

**EXPECTED_CHECKPOINT_BYTES_VERIFIED; STATIC_METADATA_INSPECTED; MODEL_NOT_EXECUTED.** Mission37 §5 authorizes this named-checkpoint identity/metadata work. AUTH35-V is not reused as a model or inference grant. Actual receipt: [CHECKPOINT_VERIFICATION_RECEIPT.json](../../../../../originals/docs/generated/master_reaudit/mission37/CHECKPOINT_VERIFICATION_RECEIPT.json).

| Binding | Actual finding |
|---|---|
| Exact checkpoint | experiments/vision/39f402dfe460/checkpoints/weights/best.pt |
| Actual and expected SHA-256 | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` — MATCH |
| Bytes / stability | 24,493,159; unchanged stat identity/size/mtime across verification |
| Archive metadata | 914 ZIP members; archive/data.pkl is 152,814 bytes |
| Stored model class | ultralytics.nn.tasks.DetectionModel; serialized Conv/C2f/SPPF/Detect structure |
| Stored class map / nc | 0 front, 1 rear, 2 side / 3 |
| Stored scale | depth_multiple 0.33, width_multiple 0.25; consistent with declared YOLOv8n |
| Frozen configuration | Same path/hash/class map in configs/frozen_experiment_v1.yaml |
| Actual model use | No deserialization, forward pass, original-frame inference or substitution |

The checkpoint was hashed once for this mission. ZIP/pickle opcode inspection used zipfile and pickletools, without executing the pickle or reconstructing tensors. Primitive metadata and opcode offsets are recorded in the receipt; full disassembly stays private at `/private/tmp/m37_checkpoint_metadata_owtf3f8e/pickle_disassembly.txt` with SHA-256 `e13bbcad9467ad8f06211e640f48bace4e6906c3d3b358a72b7c75501b022d13`. A stored class name and scale establish serialized metadata, not successfully instantiated architecture, numerical validity, trained accuracy or class-direction validity. The earlier single-class/class-role historical conflict is not resolved by a class-name dictionary. No development dataset, other checkpoint, cache or protected review was opened. No replacement weights or model were downloaded.

Actual installed environment: Python 3.11.15; Torch 2.13.0; torchvision 0.28.0; Ultralytics 8.4.121; OpenCV 5.0.0.93; NumPy 2.4.6; PyAV 18.1.0. CUDA unavailable; MPS available; the frozen requested device remains CPU. Installed packages and available compute are not model execution acceptance. PyAV was installed for the authorized PTS implementation/fixture checks; it is declared as optional `pts` extra (`av>=18.1,<19`). `python -m pip check` passes. No model download occurred.

Frozen YAML raw SHA-256 stays `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a`; canonical semantic SHA-256 stays `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`. Policy raw SHA-256 stays `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`; its reference matches the semantic hash. These distinct hash definitions are not a configuration mismatch. No thresholds/configuration were edited.

Static inspection avoids executing serialized objects, consistent with [PyTorch serialization guidance](https://docs.pytorch.org/docs/stable/notes/serialization). A future authorized run must bind its actual loader, arguments, CPU/seed/preprocessing and observed class map to these verified bytes, and preserve actual loader failures. This mission supplies no inference or checkpoint-lineage rights grant.
