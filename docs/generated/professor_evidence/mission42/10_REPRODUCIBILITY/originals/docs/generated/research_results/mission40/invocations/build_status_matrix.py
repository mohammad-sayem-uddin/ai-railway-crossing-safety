from pathlib import Path
import collections,csv,json
R=Path.cwd();D=R/'docs/generated/research_results/mission40';previous=list(csv.DictReader((R/'docs/generated/research_results/mission39/EXPERIMENT_EXECUTION_MATRIX.csv').open()));original=list(csv.DictReader((R/'docs/generated/master_reaudit/mission31/EXPERIMENT_MASTER_REGISTER.csv').open()))
assert len(previous)==156 and {r['activity_id'] for r in previous}=={r['experiment_id'] for r in original}
truth={'M31-VISION-FPFN','M31-CENSOR-T0','M31-ENGINE-IDENTITY','M31-HUMAN-COHORT','M31-EVENT-M4','M31-EVENT-M5','M31-EVENT-MTR','M31-T1-BOUNDARY','M31-EVENT-TIMING','M31-CONTROL-EXPOSURE','M31-EVENT-ERRORS','M31-TECH-GT-PROMOTION'}
rows=[]
for old in previous:
 r=dict(old);r['mission39_classification']=r.pop('classification');r['mission39_execution_state']=r.pop('execution_state');identity=r['activity_id'];c=r['mission39_classification'];scope='No new original experiment; preserve exact prior role/scope';gt=False;operation='NONE_FOR_CURRENT_DOCUMENTARY_STATUS';remaining=r['remaining_dependencies']
 if c=='SCIENTIFICALLY_UNDEFINED':status='SCIENTIFICALLY_UNDEFINED'
 elif c=='SUPERSEDED_OR_INVALID':status='SUPERSEDED_OR_INVALID'
 elif c=='DEFERRED_BY_RESEARCHER':status='DEFERRED_BY_RESEARCHER'
 elif c=='EXECUTABLE_NOW':status='COMPLETED_WITH_LIMITATIONS';scope='Earlier bounded software/support evidence retained; current relevant complete validation run executed, not a new empirical result'
 elif identity=='M31-NEXT-B2_front':
  status='BLOCKED_BY_OPERATION_SCOPE';gt=True;operation='AUTH-DESCRIPTIVE-EVAL-EXEC for exact B2 manifest/event/protocol/metric/config and valid promotion receipt';scope='Actual M39 paired-input assembly5/5 complete; real M40 boundary refused before decision replay';remaining='Current descriptive authorization and accepted source-linked canonical reference/promotion are absent; existing actual inputs verified without fabrication'
 elif identity in {'M31-NEXT-B0_front','M31-NEXT-B0_back','M31-NEXT-B1_audio'}:
  status='BLOCKED_BY_CANONICAL_GT';gt=True;operation='Current existing operation-specific descriptive replay/evaluation binding';scope='M39 original inference5/5 complete and reused unchanged; M40 raw descriptors verified';remaining='Reference-dependent comparison requires actual accepted fields/eligibility and current exact evaluation bindings; no inference rerun'
 elif identity in truth:
  status='BLOCKED_BY_CANONICAL_GT';gt=True;scope='Existing raw source/output descriptors retained where available; scientific endpoint not established';remaining='No sufficient active accepted canonical state/value records or promotion receipt; actual replay/exposure/eligibility as required by this endpoint'
 elif identity=='M31-HUMAN-PILOT':
  status='INCOMPLETE';gt=True;scope='Current five-front review remains researcher-reported complete, exact agreement reported, no separate originals stored';remaining='Original full ten-source canonical pilot coverage/recorded acceptance not established; preserve report without AI reconstruction or a repeat-review request'
 elif identity in {'M31-VISION-CONFIDENCE','M31-AUDIO-FEATURES','M31-TECH-BACK-MAPPING'}:
  status='INCOMPLETE';scope={'M31-VISION-CONFIDENCE':'Actual prediction scores are available; truth-linked trailing-car continuity/dropout not evaluable','M31-AUDIO-FEATURES':'M39 concrete V3 natural-log/normalization parity fixed/tested; other historical feature/run lineage not newly reproduced','M31-TECH-BACK-MAPPING':'Existing independent camera_2 producer executed; no invented back class-to-clearance mapping'}[identity]
  gt=identity=='M31-VISION-CONFIDENCE';remaining=r['remaining_dependencies']+'; no full activity closure inferred from a completed partial stage'
 elif identity=='M31-TECH-CACHE-PROVENANCE':
  status='COMPLETED_WITH_LIMITATIONS';scope='Current actual five-event saved payload/manifests/code/config identities verified before read-only reuse';remaining='Historical unrelated cache/registry completion not certified; no claim of source authenticity from a derived digest'
 else:
  status='BLOCKED_BY_GENUINE_INPUT';scope='Bounded prior findings retained; no unprovided historical/original evidence manufactured'
 r.update(classification=status,completed_scope=scope,remaining_dependencies=remaining,canonical_GT_required_for_remaining_stage='YES' if gt else 'NOT_UNIVERSAL_OR_ACTIVITY_SPECIFIC',current_operation_binding=operation,Mission40_original_experiment_executed='NO',Mission40_actual_scope='READ_ONLY_SAVED_OUTPUT_ANALYSIS_AND_GUARDED_SOFTWARE_VALIDATION')
 rows.append(r)
with (D/'COMPLETE_EXPERIMENT_STATUS_MATRIX.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
counts=dict(collections.Counter(r['classification'] for r in rows));summary=dict(schema='mission40-experiment-status-reconciliation/1',original_register_rows=156,retained_unique_activity_ids=156,status_counts=counts,current_defined_experiment_directions=5,prior_original_inference_stages_complete=3,prior_B2_input_assembly_complete=True,current_full_B2_decision_replays_complete=0,accepted_GT_evaluations_complete=0,new_original_experiments_Mission40=0,actual_original_events_processed_Mission40=0,actual_decision_frames_processed_Mission40=0,optional_R04='DEFERRED_NOT_ACTIVATED_EXACT_ELEVEN_EVENT010_EXCLUDED',activity_rows_are_not_independent_experiments=True,unexecuted_B2_result_file_must_be_absent=True)
(D/'EXPERIMENT_STATUS_RECONCILIATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
