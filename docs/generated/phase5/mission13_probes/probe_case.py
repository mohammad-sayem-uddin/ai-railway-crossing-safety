import sys, pathlib
sys.dont_write_bytecode=True
from railway_detection.safety import media_guard as mg
from railway_detection.evaluation import descriptive_exec_gate as dg
real=mg.REAL_REPO_ROOT; print("REAL_REPO_ROOT", real)
alt=pathlib.Path(str(real).replace("Train_automation","train_automation"))
print("alt exists (case-insensitive FS?):", alt.exists(), "| alt.resolve() == REAL:", alt.resolve()==real, "| resolved:", alt.resolve())
def code(fn):
    try: fn(); return "RETURNED (no exception => gate skipped/allowed)"
    except Exception as e: return f"{type(e).__name__}: {str(e)[:100]}"
print("descriptive gate, canonical root :", code(lambda: dg.require_descriptive_authorization_for_engine(real, condition=None, event_id="e", manifest_sha256="0"*64)))
print("descriptive gate, case-variant   :", code(lambda: dg.require_descriptive_authorization_for_engine(alt, condition=None, event_id="e", manifest_sha256="0"*64)))
fake=alt/"data/raw/layer_b/train_events/__m13_fake__/front.mov"
print("media guard, case-variant FAKE path:", code(lambda: mg.require_media_authorization(fake,"READ_RAW_MEDIA")))
print("media guard, is_synthetic_location(case-variant):", mg.is_synthetic_location(fake))
