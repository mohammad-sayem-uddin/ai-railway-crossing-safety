"""Bounded documentary/source intake; does not read original media or checkpoints."""
from pathlib import Path
import hashlib,json,subprocess
from railway_detection.safety.resource_free_acceptance import bindings
R=Path.cwd();D=R/'docs/generated/research_results/mission40';M=R/'docs/generated/research_results/mission39';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip();assert head=='c4d65916128dcc12857e4e5b89f98452e118d9c9';assert subprocess.check_output(['git','branch','--show-current']).decode().strip()=='main'
prior=load(M/'audio_followup/FOLLOWUP_DELIVERY_VALIDATION.json')
for rel,h in prior['artifact_sha256'].items():assert sha(M/rel)==h,rel
old=load(M/'audio_followup/FOLLOWUP_BASELINE_AND_BINDING.json')
for rel,h in old['original_seven_researcher_sha256'].items():assert sha(R/rel)==h
full=load(M/'audio_followup/software_validation/CORRECTED_CODE_FULL_RUN_RECEIPT.json');assert bindings(R)==full['source_bindings']
paths=subprocess.check_output(['git','ls-files','-z','docs/generated/master_reaudit','docs/generated/research_results/mission39']).decode().strip('\0').split('\0')
baseline=dict(schema='mission40-baseline/1',branch='main',starting_commit=head,tracking=subprocess.check_output(['git','rev-parse','origin/main']).decode().strip(),status=subprocess.check_output(['git','status','--short']).decode(),previous_documentary_artifact_sha256={p:sha(R/p) for p in paths},original_seven_researcher_sha256=old['original_seven_researcher_sha256'],source_bindings=bindings(R),request_path='/Users/sayemuddin/.codex/attachments/0b7e451b-b423-45e7-93f1-8bcb9316d71b/Pasted text.txt',request_sha256=sha('/Users/sayemuddin/.codex/attachments/0b7e451b-b423-45e7-93f1-8bcb9316d71b/Pasted text.txt'),Mission39_artifact_hashes_verified=len(prior['artifact_sha256']),original_media_or_model_access=False)
(D/'BASELINE_AND_PRESERVATION.json').write_text(json.dumps(baseline,indent=2)+'\n')
print(json.dumps(dict(head=head,prior_artifacts_pinned=len(paths),Mission39_hashes_verified=len(prior['artifact_sha256']),original_seven_hashes_match=True,source_bindings_equal_completed_Mission39_run=True)))
