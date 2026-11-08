"""Complete the bounded descriptor/admission package from retained real outputs."""
from pathlib import Path
import collections,csv,hashlib,json,os,tempfile
R=Path.cwd();D=R/'docs/generated/research_results/mission41';P=R/'docs/generated/research_results/mission40';M=R/'docs/generated/research_results/mission39';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();load=lambda p:json.loads(Path(p).read_text())
run=load(D/'DESCRIPTIVE_EXECUTION_RECEIPT.json');prep=load(D/'B2_UNISSUED_AUTHORIZATION_PREPARATION.json');admission=load(D/'B2_CURRENT_ADMISSION_RECEIPT.json');baseline=load(D/'BASELINE_AND_PRESERVATION.json');raw=list(csv.DictReader((D/'B2_INPUT_AUDIO_RECORD_RUNS.csv').open()));breakdown=[]
for event in prep['candidate_fields']['scope']['events']:
 rr=[r for r in raw if r['event']==event and r['input_record_state']=='NO_AUDIO_RECORD_IN_INPUT_WINDOW'];prefix=[r for r in rr if int(r['first_input_frame_index'])==0];later=[r for r in rr if int(r['first_input_frame_index'])!=0];assert len(prefix)==1 and int(prefix[0]['input_frames_in_run'])==5 and all(int(r['input_frames_in_run'])==1 for r in later)
 breakdown.append(dict(event=event,initial_no_audio_record_frames=5,initial_last_assembly_time_s=prefix[0]['last_assembly_time_s'],first_causal_audio_window_end_s=1.0,later_single_frame_absence_runs=len(later),later_no_audio_record_frames=len(later),total_no_audio_record_input_frames=5+len(later),decision_frames='NOT_EXECUTED',interpretation='Existing input stage only; no padding or negative-evidence substitution'))
assert sum(r['total_no_audio_record_input_frames'] for r in breakdown)==445
with (D/'B2_INPUT_RECORD_ABSENCE_BREAKDOWN.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(breakdown[0]),lineterminator='\n');w.writeheader();w.writerows(breakdown)
# Retain every activity and its prior missing-input context while using the Mission41 vocabulary.
rows=list(csv.DictReader((P/'COMPLETE_EXPERIMENT_STATUS_MATRIX.csv').open()))
for row in rows:
 previous=row['classification'];row['mission40_classification']=previous
 if previous=='BLOCKED_BY_GENUINE_INPUT':row['classification']='INCOMPLETE'
 row['Mission41_new_original_experiment']='NO';row['Mission41_descriptor_scope']='No new applicable descriptor beyond retained evidence'
 if row['activity_id'] in ['M31-VISION-CONFIDENCE','M31-EVENT-TIMING','M31-NEXT-B1_audio','M31-NEXT-B2_front','M31-TECH-DATA-VALIDATION','M31-TECH-REPRO-BINDING']:
  row['Mission41_descriptor_scope']='Existing model-only descriptor processing complete at five-event scope; truth/remaining activity requirements retained'
 if row['activity_id']=='M31-NEXT-B2_front':row['remaining_dependencies']='Absent current AUTH-DESCRIPTIVE-EVAL-EXEC; absent accepted-reference promotion receipt; absent live canonical protocol binding. Three hashes known, selected M4 candidate retained without re-adoption. Narrow unissued field preparation supplied.'
 row['current_operation_binding']=row['current_operation_binding'].replace('valid promotion receipt','valid promotion receipt and live protocol profile')
assert len(rows)==156 and len({r['activity_id'] for r in rows})==156
with (D/'MISSION_41_EXPERIMENT_COMPLETION_MATRIX.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
status_counts=dict(collections.Counter(r['classification'] for r in rows))
for name in ['COMPLETED_VALID','BLOCKED_BY_TECHNICAL_DEFECT']:status_counts.setdefault(name,0)
(D/'EXPERIMENT_STATUS_RECONCILIATION.json').write_text(json.dumps(dict(original_activity_rows=156,status_counts=status_counts,current_scientific_directions=5,original_inference_stages_complete_with_limitations=3,B2_input_assembly_complete=True,B2_decision_replay_complete=False,new_original_experiments=0,accepted_GT_evaluations=0,completed_model_only_descriptor_families=5,scope='Five physical events; activity rows are not independent experiments',M40_genuine_input_category_mapping='31 rows become INCOMPLETE under the requested Mission41 vocabulary, with exact prior missing-input reasons retained; not resolved',optional_R04='Not activated; exactly eleven; event_010 excluded'),indent=2)+'\n')
# A proposed freeze pins bounded results; it is not researcher scientific acceptance.
freeze=dict(schema='mission41-bounded-descriptive-freeze/1',status='BOUNDED_MODEL_OUTPUT_DESCRIPTORS_READY_FOR_RESEARCHER_REVIEW',researcher_accepted=False,source_delivery_commits=['c4d65916128dcc12857e4e5b89f98452e118d9c9','e82269521c1222fef0826449e18a386a7a58a362'],physical_events=5,unique_camera_members=10,source_payload_sha256=run['source_payload_sha256'],reused_completed_tables=run['reused_completed_tables'],descriptor_artifact_sha256={p.name:sha(p) for p in D.glob('*.csv') if p.name!='MISSION_41_EXPERIMENT_COMPLETION_MATRIX.csv'},frozen_config_canonical_sha256=prep['candidate_fields']['bindings']['model_config_provenance_sha256'],checkpoint_identities=prep['model_identities'],checkpoint_identity_basis='Existing actual Mission39 verification, not a fresh checkpoint read/hash',B2_decision_replay=False,ACCEPTED_CANONICAL_GT='NOT_ESTABLISHED',metric_scope='Model-output/source-clock/observed processing-time/input-record descriptors only; no GT performance, fusion superiority or safety result',operational_or_release_authorization=False,raw_inference_repeated=False,source_time_and_processing_time_distinguished=True)
(D/'BOUNDED_DESCRIPTIVE_RESULTS_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
(D/'B2_EXECUTION_ADMISSION_ANALYSIS.md').write_text(f'''# Exact B2 execution admission

**Requirements identified; execution admission remains unsatisfied.** The current real-root call returns AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED before decision processing. The algorithm can compute raw state transitions without human GT, but this existing governed operation intentionally requires accepted-reference promotion and a fixed metric bundle. That distinction is maintained; no alternate engine route, fake root or guard modification is used.

Required object: data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json, schema phase5-descriptive-eval-execution-authorization/1. Operation: **descriptive_cache_only_replay**; condition **B2**, exact five existing pilot events. The [unissued preparation](B2_UNISSUED_AUTHORIZATION_PREPARATION.json) has the exact allowed candidate field sets and ten actual cache references with hashes/sizes/rows. It is outside the canonical directory, labeled UNISSUED_NOT_EXECUTABLE; null fields make it deliberately invalid for execution. No canonical record is created.

| Required binding | Verified/prepared value | Current standing |
|---|---|---|
| evaluation_manifest_sha256 | {prep['candidate_fields']['bindings']['evaluation_manifest_sha256']} | Actual five-event front/audio manifest and all ten payloads verified |
| metric_scope_sha256 | {prep['candidate_fields']['bindings']['metric_scope_sha256']} | Exact existing nine-field metric set |
| model_config_provenance_sha256 | {prep['candidate_fields']['bindings']['model_config_provenance_sha256']} | Unchanged parsed frozen configuration; prior model verification reused |
| promotion_receipt_sha256 | null | Actual accepted-reference promotion receipt absent |
| protocol_sha256 | null live value | Canonical protocol-choice record absent; effective-profile routine has no premature-opening default |

The already selected M4 choice is retained, not reopened: first_blocked_to_t4_clearance. Its candidate effective-profile hash is {prep['already_selected_M4_candidate_profile_sha256']}. That computed candidate is not a live canonical protocol binding, and is never substituted for one. The code's stale unresolved-default state is a missing record/binding issue here, not authority to reselect RD014 or adopt a new scientific definition.

Mandatory record fields are schema_version, authorization_id, authorization_class, status, authorized_by, authorized_at_utc, expires_at_utc, revoked, authorization_statement, attestation, recorded_by, scope, bindings and record_sha256. The actual schema requires APPROVED, an allowlisted authority, nonfuture issuance/current expiry, revoked=false, an exact canonical digest, RECORDED_RESEARCHER_STATEMENT with signature=null, and an identified agent_transcription source where used. It does **not** require a fabricated handwritten signature. Scope must name the operation, B2 only, five explicit events, exact metric set, local research purpose and field_or_physical_operations_authorized=false.

The researcher's existing Mission41 direction and previously confirmed authority attribution supply scoped intent and statement provenance. Another generic “yes” would not supply a legitimate promotion receipt or the absent live protocol binding, so no redundant approval question is asked. Approval/issue dates, expiry and seal are left unissued. The promotion receipt cannot be created from human–AI agreement or absent original notes. No authority allowlist or existing operation selection changes.

The fixed metric scope is blocked_seconds, clearance_latency_s, closure_episodes, excess_closed_duration_s, exposure_s, missed_train, premature_opening, total_closed_s and warning_lead_time_s. Schema1 rejects a metric subset and exposes no decision-only alternative. Broad live-binding evaluation calls official-readiness checkpoint hashing; it was not invoked merely to reproduce a known missing input. Source/config/reference text inspection and the real early refusal are sufficient to identify the current blockers without repeat inference/checkpoint verification. [Current admission receipt](B2_CURRENT_ADMISSION_RECEIPT.json).

Frozen settings are preserved. A future accepted invocation can supply the existing MultimodalDecisionEngine(config=frozen_config) argument; no production logic change is currently justified. The input collector's0.25s window differs from replay's0.5s window. The1079/634/445 input counts are not assumed to be decision-frame counts. No request for future experiments, new data, raw access, training, release, physical railway operations or blanket permission is made.
''')
(D/'REFERENCE_AND_GT_STATUS.md').write_text('''# Reference and GT status

**ACCEPTED_CANONICAL_GT=NOT_ESTABLISHED.** The32 relevant reference/proposal/invalidation texts remain byte-identical to the inspected Mission40 set. The current notice-aware reader finds no active unexcused records; no promotion receipt exists. Invalidated legacy schema6 records stay invalidated, and AI proposals remain comparison references. [Integrity receipt](REFERENCE_INTEGRITY_RECEIPT.json).

The researcher and classmate reportedly completed separate first passes on all five front recordings, then reported exact agreement with each other and AI annotations. This positive researcher-reported account is preserved, including the classmate's partial familiarity. Separate original observations were not stored. No review is repeated or requested; no individual observation, boundary, signature, competence record, time or canonical parent is reconstructed. These facts do not automatically produce accepted GT or a promotion receipt.

M4/M5/MTR/T1-warning, control/engine truth-based outcomes, correctness/FP/FN/precision/recall/F1, human agreement metrics and boundary censoring/uncertainty remain unavailable with null denominators. Model-only output descriptors remain valid at their stated limited scope. No scientific endpoint is zero-filled; no external account/private notes search, original media inspection or renewed source inventory is undertaken.
''')
# Actual new descriptor findings, kept separate from already completed tables.
absence_table='\n'.join(f"| {r['event']} | {r['initial_no_audio_record_frames']} | {r['later_no_audio_record_frames']} | {r['total_no_audio_record_input_frames']} |" for r in breakdown)
(D/'REMAINING_DESCRIPTIVE_ANALYSIS.md').write_text(f'''# Remaining model-only descriptive analysis

Five existing descriptor families were processed from saved outputs, without new inference/replay. Each is mapped to existing Mission31 plan IDs in [the execution register](DESCRIPTIVE_EXECUTION_RECEIPT.json), with exact command, invocation/input hashes and exclusions. Previously completed per-event/per-class tables are reused by hash; no duplicate experimental total is added.

| Existing activity | New retained processing | Interpretation |
|---|---|---|
| Visual confidence continuity/output distributions |40 source/class summaries,78 consecutive-sample runs | Literal model labels; ANY overlaps class-specific summaries and is never summed as extra objects |
| Native sampled-clock diagnostics |28 interval-frequency rows across ten visual and five acoustic streams | Source-local presentation intervals and frozen audio hop, not physical synchronization |
| Supporting audio output continuity |74 consecutive model-label runs spanning423 windows | Correlated windows at frozen0.37; not74 horns/trains or accuracy |
| B2 input-record absence detail |847 present/absent runs, plus five-event absence breakdown | Input collector only, not decision replay or fabricated negative evidence |
| Existing processing-time summaries |15 retained member times, three aggregate rows | Different measured scopes; no new timing run or controlled speed comparison |

[Visual runs](VISUAL_SAMPLE_RUNS.csv) preserve actual sample indices/native integer PTS/timebase. [Confidence summaries](VISUAL_CONFIDENCE_CONTINUITY_SUMMARY.csv) retain zero model-output rows and unavailable scores where no output exists. Contiguous means adjacent selected rows, with no new temporal-gap threshold; endpoint span is not continuous occupancy or true trailing-car dropout. [Audio runs](AUDIO_MODEL_LABEL_RUNS.csv) retain integer window sample bounds and causal ends; ambient is a model label, not proof of train/horn absence.

[Sampled-clock intervals](SAMPLED_CLOCK_CADENCE.csv): front observed selected-row intervals range0.1683333333–0.2016666667s; back0.185–0.2016666667s; audio hop exactly0.5s. These are observed sampled presentation intervals, not a measurement of source capture FPS, VFR diagnosis, physical camera alignment or clock error. Front/back native clocks are not shifted or fused. Model/source time and processing wall time remain separate.

## The445 audio-empty input frames

| Existing event | Before first causal audio output | Later single-frame input gaps | Total input frames without audio record |
|---|---:|---:|---:|
{absence_table}

There are five initial absence runs of five frames (25 total, assembly time0 through0.8s before the first causal window end1.0s), and420 later single-frame gaps. Together they account for exactly445 input frames. Presence runs are212 two-frame runs and210 one-frame runs, totaling634 paired inputs. [Exact breakdown](B2_INPUT_RECORD_ABSENCE_BREAKDOWN.csv), [full run table](B2_INPUT_AUDIO_RECORD_RUNS.csv), [figure](figures/B2_INPUT_ABSENCE_BREAKDOWN.png).

These records remain absent; no padding, interpolation or negative evidence is supplied. The later pattern belongs to the existing0.25s input collector with0.5s audio hop and0.2s assembly grid. Actual replay uses a different0.5s collector window, so the audio-empty decision-frame count remains unknown until authorized execution. This diagnostic does not run or substitute for replay.

[Processing-time detail](EXISTING_PROCESSING_TIME_DETAIL.csv) and [aggregates](EXISTING_PROCESSING_TIME_AGGREGATES.csv) reuse observed sums: front98.308s/back174.395s/audio1.983s. Audio measurement includes clock decode/conversion/inference/serialization/B2 assembly and excludes initialization/superseded attempts; visual scopes differ. These are prior observed processing times, not a new benchmark, deployment/real-time claim or fair cross-modality speed comparison. Engine and control remain separate rows; all-frame counts are not independent event denominators.

Existing class output tables stay unchanged (front13 objects:2 front/0 rear/11 side; back276:40 front/4 rear/232 side). Supporting audio has120 of423 model scores≥0.37, not a measured detection rate or correctness. No new inferential tests, scientific cutoffs, labels, metrics, GT boundaries or performance comparison are introduced.
''')
(D/'FINAL_RESEARCH_STATUS.md').write_text(f'''# Final research status

**BOUNDED_MODEL_OUTPUT_DESCRIPTORS_READY_FOR_RESEARCHER_REVIEW; B2_DECISION_ADMISSION_UNSATISFIED; ACCEPTED_CANONICAL_GT=NOT_ESTABLISHED.**

| Existing scientific direction | Completed scope | Current remaining scope |
|---|---|---|
| B0_front | Five-front actual inference and bounded descriptors | Accepted-reference evaluation/current bindings |
| B0_back | Five-back independent actual inference and bounded descriptors | Supported adopted clearance/replay binding and accepted reference |
| B1_audio | Five-front actual supporting acoustic inference and bounded descriptors | Legitimate acoustic truth/eligibility for correctness |
| B2_front | Five-event actual paired inputs and missing-record diagnostics | Current promotion/protocol-bound authorization; no decision replay |
| R04 | Existing optional exact-eleven definition | Separately adopted/accepted scope; not activated, event_010 excluded |

Three original inference stages and the B2 input stage remain complete with limitations. No additional original experiment or accepted-GT evaluation is claimed. All156 activity IDs are retained in [the matrix](MISSION_41_EXPERIMENT_COMPLETION_MATRIX.csv); category counts are {json.dumps(status_counts,sort_keys=True)}. Mission40's31 genuine-input rows map to INCOMPLETE under this mission's vocabulary with their exact dependency text retained; the mapping does not close them. Activity counts are not independent experiments or universal pilot requirements.

The [bounded freeze manifest](BOUNDED_DESCRIPTIVE_RESULTS_FREEZE.json) pins saved payloads, derived descriptors, reused tables and unchanged config/model identities for researcher review. It is ready for a limited model-output/input feasibility freeze with explicit omissions. It is not researcher acceptance, an execution/release grant, a fully evaluated pilot, a B2 result or a professor evidence folder.

M4 primary/M5 integer companion/MTR feasibility, independent-camera primary, exploratory fusion/supporting audio, source-clock/censoring/uncertainty rules remain. T2/occupancy/RD046/comparator/deployment/hardware and unadopted training/splits/directions are not activated. No safety, accident reduction, all-weather/cross-site, real-time, deployment or fusion-superiority claim is supported.
''')
(D/'NEXT_PHASE_RECOMMENDATION.md').write_text('''# Next phase recommendation

Review and, if accepted by the researcher, freeze the bounded saved-model-output descriptor set using BOUNDED_DESCRIPTIVE_RESULTS_FREEZE.json and its explicit omissions. No repeat inference, same-person review, replacement recording, additional source inventory or generic authorization audit is needed for that scope.

Existing B2 replay can advance when genuine accepted-reference promotion and the live canonical protocol binding are available, then the narrow current operation record can be completed through its existing schema. B2_UNISSUED_AUTHORIZATION_PREPARATION.json supplies the exact candidate fields, three known hashes, five event scopes and missing facts. The selected M4 profile is retained, not re-asked. Another blanket permission reply does not replace a promotion receipt; current scope intent/identity are already recorded as evidence.

No GT or signature/date is fabricated to finish the record, and the gate is not weakened or bypassed. Raw decision computation is conceptually reference-free, but this existing governed operation is promotion-bound and has a fixed nine-field metric scope; no separate model-only operation is adopted here. Leave its result unavailable until genuinely admitted. Keep optional R04 separate and exactly eleven with event_010 excluded.

After genuine admission, use the original byte-bound visual/audio inputs and frozen configuration, preserve causal native clocks and missing records, then calculate only legitimately eligible endpoints. Professor/manuscript work stays paused pending researcher review and a separate instruction. No new scientific direction or engineering rebuild is proposed.
''')
(D/'MISSION_41_FINAL_REPORT.md').write_text(f'''# Mission41 final report

Prepared2026-11-08, America/New_York. **PERMITTED_DESCRIPTIVE_WORK_COMPLETE; B2_NOT_ADMITTED; ACCEPTED_CANONICAL_GT=NOT_ESTABLISHED.** Exact existing authorization fields are prepared without issuance; five missing descriptor families are completed from saved actual outputs. No original inference, production change, new scientific experiment or test-suite rerun occurs.

## Direct answers to the15 requested questions

1. **Boundary resolved?** Its exact requirements and missing facts are identified; actual execution admission remains unsatisfied. Real-root replay still refuses before decisions. [Admission analysis](B2_EXECUTION_ADMISSION_ANALYSIS.md), [receipt](B2_CURRENT_ADMISSION_RECEIPT.json).
2. **Exact missing fields/bindings?** Canonical AUTH-DESCRIPTIVE-EVAL-EXEC object for descriptive_cache_only_replay/B2/five events is absent. promotion_receipt_sha256 cannot be verified because its genuine receipt is absent; protocol_sha256 has no live value because the canonical protocol-choice record is absent. Three other hashes are prepared. Selected M4 is retained with a candidate profile hash, never substituted for the missing live binding.
3. **B2 executed?** No. No approved record, signature, time or promotion is fabricated; no guard or metric scope is changed.
4. **Events/decision frames?** Zero new original events and zero decision frames. Saved descriptors cover the same five physical events/ten camera members,2179 visual records/423 audio windows/1079 input frames.
5. **Actual decisions/outputs?** No B2 decisions or result file. Actual new outputs are confidence/run/cadence/timing/input-gap tables and their source/hash receipts, not replay outputs.
6. **Paired frames?**634 existing input frames contain both streams; this is not a measured paired-decision count.
7. **The445 input frames without audio?**25 occur before the first causal audio output (five per event);420 later singleton gaps remain absent. No negative substitution or padding; replay uses a different collector window, so actual replay missingness is not inferred.
8. **Independent descriptions completed?**40 visual source/class continuity summaries/78 sampled-output runs,28 sampled-clock interval rows,74 model-label audio runs,847 input-record runs/five absence-breakdown rows,15 reused timing details/three aggregates. [Analysis](REMAINING_DESCRIPTIVE_ANALYSIS.md), [execution register](DESCRIPTIVE_EXECUTION_RECEIPT.json). Previously completed tables are reused, not counted as new experiments.
9. **Reference-dependent unavailable metrics?** M4/M5/MTR/T1-warning, correctness/FP/FN/precision/recall/F1, control/engine truth outcomes, human agreement and boundary censoring/uncertainty. Nulls remain unavailable, not zero.
10. **Genuine canonical reference discovered?** No active unexcused record or promotion receipt;32 relevant texts match the prior inspection. Reported human review remains supporting evidence with separate originals not stored and classmate familiarity preserved. [Reference status](REFERENCE_AND_GT_STATUS.md).
11. **Production defects fixed?** None demonstrated or changed. The boundary is an intentional governed scope requirement, not permission to remove promotion. Frozen defaults can be explicitly passed through the existing engine argument; no new threshold/logic is introduced.
12. **The115 inherited tests?** Unchanged tested source/config/test bindings reuse Mission40:3700 passed,84 failed,31 errors,0 skipped;115 are the nonpassing subset. No tests executed anew or full-suite rerun; only saved-artifact/schema/integrity checks run.
13. **Five directions?** Three inference stages complete with limitations; B2 input stage complete/decision stage blocked; R04 optional/deferred. [Current156-row matrix](MISSION_41_EXPERIMENT_COMPLETION_MATRIX.csv).
14. **Scientific work remaining?** Genuine canonical reference/promotion and live protocol/operation bindings for the existing B2/evaluation route, then actual admitted replay and eligible metrics. Broader historical/deferred items are not turned into compulsory experiments. No repeat same-person review or missing-note reconstruction requested.
15. **Bounded descriptive-results freeze ready?** Yes, for saved model-output/input feasibility descriptors with explicit omissions and researcher review. [Freeze manifest](BOUNDED_DESCRIPTIVE_RESULTS_FREEZE.json). It is not acceptance of GT, complete B2/performance validation or permission for external handoff.

## Exact scope, software and preservation

Started main at {baseline['starting_commit']}; origin/main remains{baseline['tracking']}, no push. [Baseline](BASELINE_AND_PRESERVATION.json) pins817 prior artifacts and verifies the Mission40 delivery/source identities and seven original researcher hashes. M39/M40 actual results and superseded diagnostics stay unchanged. Only Mission41 documentary/analysis invocation artifacts are created; src/scripts/tests/config/schema/gates remain unchanged. Existing checkpoint verification is reused, not repeated.

The smallest [unissued record preparation](B2_UNISSUED_AUTHORIZATION_PREPARATION.json) preserves the supported key sets and exact B2 source/manifest/model/config scope. Current instruction supplies scope intent and previously confirmed authority attribution. The actual schema accepts a recorded unsigned researcher statement with signature=null; no additional pen signature or blanket approval is required. Missing evidentiary bindings, not a fresh generic confirmation, prevent honest issuance. No question is asked that could falsely imply a permission reply creates GT or promotion. The selected M4 profile is not reopened.

No SOFTWARE_REGRESSION_VALIDATION report is created because no regression tests run. Mission40's completed3815-case evidence remains historical tested-code evidence, not a fresh Mission41 pass count. Relevant current source/input/reference/schema consistency is checked; Python checks are not OS isolation. Raw source/model/media/GT/promotions, new inference/replay, training/calibration/splits/hardware/actuation, external contact or release are not performed.

RD001–055/27 selections, five-event pilot/27-candidate cohort/two duplicate exclusions, independent cameras/exploratory fusion/supporting audio, M4 primary/M5 companion/MTR feasibility and per-metric denominators/censoring/uncertainty remain. T2/occupancy/RD046/comparator stay deferred/inactive; R04 remains optional exact-eleven, event_010 excluded. No new thresholds/inferential tests/labels/GT shift/invented exit/duration padding, source inventory, browser rebuild, professor folder or manuscript.

Only exact Mission41 paths are staged and committed locally after checks. Seven researcher changes and existing private caches remain unstaged; no broad staging/reset/clean/amend/rebase/history rewrite/push. The containing commit hash and final worktree are verified after commit. [Final status](FINAL_RESEARCH_STATUS.md), [next phase](NEXT_PHASE_RECOMMENDATION.md).
''')
for p in D.glob('*.md'):
 s=p.read_text()
 for a,b in {'Prepared2026':'Prepared 2026','the15':'the 15','remainsfc3':'remains fc3','the445':'the 445','The445':'The 445','the1079':'the 1079'}.items():s=s.replace(a,b)
 p.write_text(s)
# One new diagnostic figure from actual saved absence rows, never a decision plot.
os.environ['MPLCONFIGDIR']=tempfile.mkdtemp(prefix='m41_figure_',dir='/private/tmp')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
(D/'figures').mkdir(exist_ok=True);fig,ax=plt.subplots(figsize=(9,4.3));labels=[r['event'].replace('_events/',' / ') for r in breakdown];x=list(range(5));ax.bar(x,[5]*5,color='#a97734',label='Before first causal audio output');ax.bar(x,[r['later_no_audio_record_frames'] for r in breakdown],bottom=[5]*5,color='#497eae',label='Later single-frame input-window gaps');ax.set_xticks(x,labels,rotation=16);ax.set_ylabel('Existing input frames without an audio record');ax.set_title('B2 input record absence — no decision replay');ax.legend();ax.spines[['top','right']].set_visible(False);fig.text(.02,.01,'25 initial + 420 later = 445 input frames. Missing records remain absent; no negative evidence or interpolation.',fontsize=8);fig.tight_layout(rect=(0,.07,1,1));fig.savefig(D/'figures/B2_INPUT_ABSENCE_BREAKDOWN.png',dpi=170);plt.close(fig)
print(json.dumps(dict(descriptor_families=5,absence_initial=25,absence_later=420,activity_rows=156,status_counts=status_counts,B2_replay=False,new_test_runs=0,freeze_status=freeze['status'])))
