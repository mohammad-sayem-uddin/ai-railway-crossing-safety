"""Inspect actual text references and invoke the real B2 admission boundary only."""
from pathlib import Path
from datetime import datetime,UTC
import hashlib,json,subprocess
from railway_detection.evaluation.cache_only_engine import CacheOnlyReplayEngine
from railway_detection.evaluation.descriptive_exec_gate import DescriptiveExecutionNotAuthorized,BINDING_KEYS,DESCRIPTIVE_METRIC_SCOPE,metric_scope_sha256
from railway_detection.evaluation.execution_gate import _read_repository_records
from railway_detection.experiments.frozen_config import load_frozen_config
R=Path.cwd();D=R/'docs/generated/research_results/mission40';M=R/'docs/generated/research_results/mission39';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
intake=load(R/'docs/generated/master_reaudit/mission38/HUMAN_REVIEW_COMPARISON_INTAKE_RECEIPT.json');prior=intake['inspection']['inspected_text_sha256'];fingerprints={p:sha(R/p) for p in prior};unchanged=[p for p,h in fingerprints.items() if h==prior[p]]
records,blockers=_read_repository_records(R)
promotion=R/'data/governance/stage21_promotion_receipt.json';auth=R/'data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json'
reference=dict(schema='mission40-reference-record-inspection/1',inspected_text_documents=len(fingerprints),all_prior32_text_fingerprints_unchanged=len(unchanged)==len(fingerprints),text_sha256=fingerprints,active_unexcused_records=len(records),active_schema_counts={},read_repository_blockers=[dict(code=b.code,detail=b.detail) for b in blockers],canonical_promotion_receipt_present=promotion.is_file(),descriptive_authorization_present=auth.is_file(),accepted_GT_fields_available=False,human_report='Reported five-front review complete and exact agreement; separate observations not stored; classmate partial familiarity retained; no repeat review or AI reconstruction',scope='Existing repository text records/notices only; no raw source/model reads, promotion execution or values reconstructed from AI')
for item in records:
 version=str(item.data.get('schema_version','UNKNOWN'));reference['active_schema_counts'][version]=reference['active_schema_counts'].get(version,0)+1
(D/'REFERENCE_RECORD_INSPECTION.json').write_text(json.dumps(reference,indent=2)+'\n')
manifest=M/'audio_followup/FRONT_AUDIO_ACTUAL_INPUT_MANIFEST.json';data=load(manifest);events=list(data['events']);assert len(events)==5
for e,entry in data['events'].items():
 for key in ['front_vision_cache','front_audio_cache']:
  spec=entry[key];p=R/spec['path'];assert sha(p)==spec['sha256'] and p.stat().st_size==spec['byte_size'];assert len(p.read_text().splitlines())==spec['line_count']
output=R/'results/replays/mission40_admission_only';before=output.exists();engine=CacheOnlyReplayEngine(manifest,repo_root=R,output_base_dir=output)
try:
 engine.execute_replay(events[0],'B2')
except DescriptiveExecutionNotAuthorized as exc:
 admission=dict(status='REFUSED_BEFORE_DECISION_REPLAY',code=exc.code,detail=exc.detail)
else:raise AssertionError('Unexpected execution without actual expected bindings; inspect actual state')
assert not promotion.exists() and not auth.exists();assert output.exists()==before
receipt=dict(schema='mission40-B2-real-admission/1',checked_utc=datetime.now(UTC).isoformat(),actual_method='CacheOnlyReplayEngine.execute_replay',repo_root=str(R),condition='B2',event_admission_attempted=events[0],all_existing_input_events=events,input_manifest_path=str(manifest.relative_to(R)),input_manifest_sha256=sha(manifest),all_actual_input_hashes_sizes_rows_verified=True,admission=admission,B2_decision_replay_executed=False,actual_events_processed=0,actual_decision_frames_processed=0,existing_input_frames=1079,existing_paired_input_frames=634,output_directory_created=False,missing_current_records=[str(auth.relative_to(R)),str(promotion.relative_to(R))],required_bindings=list(BINDING_KEYS),metric_scope=list(DESCRIPTIVE_METRIC_SCOPE),metric_scope_sha256=metric_scope_sha256(),frozen_config_sha256=load_frozen_config().canonical_hash,gate_removed_or_patched=False,new_authorization_or_GT_records_created=False,raw_media_or_model_access=False,real_input_replay_in_synthetic_root=False)
(D/'B2_REPLAY_ADMISSION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(admission=admission,active_reference_records=len(records),promotion_present=promotion.exists(),all_32_reference_hashes_unchanged=reference['all_prior32_text_fingerprints_unchanged'],events_processed=0)))
