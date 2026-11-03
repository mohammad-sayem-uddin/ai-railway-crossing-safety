import sys, pathlib
sys.dont_write_bytecode=True
from railway_detection.evaluation.evaluation_runner import Phase12EvaluationRunner as R, EvaluationRefused
root=pathlib.Path("/Users/sayemuddin/Desktop/Train_automation")
for label,out in (("canonical protected", root/"data/ground_truth/__m13_probe__"),
                  ("case-variant protected dir", root/"data/Ground_Truth/__m13_probe__"),
                  ("case-variant repo prefix", pathlib.Path("/Users/sayemuddin/Desktop/train_automation/data/ground_truth/__m13_probe__"))):
    try:
        d=R._checked_output_dir(root,out); print(f"{label}: ACCEPTED -> {d}  (no directory was created; function is read-only)")
    except EvaluationRefused as e: print(f"{label}: REFUSED {e.code}")
