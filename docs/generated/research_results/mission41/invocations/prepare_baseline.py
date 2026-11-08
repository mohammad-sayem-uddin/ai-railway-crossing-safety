"""Pin known documentary artifacts and unchanged tested code, without raw source I/O."""
from pathlib import Path
import hashlib,json,subprocess
from railway_detection.safety.resource_free_acceptance import bindings
R=Path.cwd();D=R/'docs/generated/research_results/mission41';P=R/'docs/generated/research_results/mission40';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();load=lambda p:json.loads(Path(p).read_text())
head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip();assert head=='e82269521c1222fef0826449e18a386a7a58a362';assert subprocess.check_output(['git','branch','--show-current']).decode().strip()=='main'
validation=load(P/'DELIVERY_VALIDATION.json')
for name,h in validation['artifact_sha256'].items():assert sha(P/name)==h,name
prior=load(P/'BASELINE_AND_PRESERVATION.json')
for name,h in prior['original_seven_researcher_sha256'].items():assert sha(R/name)==h
full=load(P/'software_validation/FULL_RUN_RECEIPT.json');assert bindings(R)==full['source_bindings']
paths=subprocess.check_output(['git','ls-files','-z','docs/generated/master_reaudit','docs/generated/research_results/mission39','docs/generated/research_results/mission40']).decode().strip('\0').split('\0')
obj=dict(schema='mission41-baseline-preservation/1',branch='main',starting_commit=head,tracking=subprocess.check_output(['git','rev-parse','origin/main']).decode().strip(),status=subprocess.check_output(['git','status','--short']).decode(),prior_artifact_sha256={p:sha(R/p) for p in paths},original_seven_researcher_sha256=prior['original_seven_researcher_sha256'],source_bindings=bindings(R),M40_full_receipt_sha256=sha(P/'software_validation/FULL_RUN_RECEIPT.json'),M40_counts=full['totals'],request_path='/Users/sayemuddin/.codex/attachments/89dc4be2-81c7-49d9-b68a-bd1ded769e78/Pasted text.txt',request_sha256=sha('/Users/sayemuddin/.codex/attachments/89dc4be2-81c7-49d9-b68a-bd1ded769e78/Pasted text.txt'),raw_source_or_checkpoint_access=False)
(D/'BASELINE_AND_PRESERVATION.json').write_text(json.dumps(obj,indent=2)+'\n');print(json.dumps(dict(head=head,prior_artifacts=len(paths),M40_artifact_hashes_verified=len(validation['artifact_sha256']),source_bindings_unchanged=True,M40_counts=full['totals'])))
