"""Summarize actual retained tests, dispositions and previously executed input evidence."""
from pathlib import Path
import collections,csv,gzip,hashlib,json,os,re,tempfile,xml.etree.ElementTree as ET
from railway_detection.safety.resource_free_acceptance import case_node
R=Path.cwd();D=R/'docs/generated/research_results/mission40';S=D/'software_validation';M=R/'docs/generated/research_results/mission39';load=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
full=load(S/'FULL_RUN_RECEIPT.json');assert full['execution_complete'] and full['source_bindings_unchanged'];assert (S/'FULL_RUN_WALL_TIME.json').exists();prior=load(M/'audio_followup/software_validation/CORRECTED_CODE_FULL_RUN_RECEIPT.json')
all_cases=[c for g in full['groups'] for c in g['cases']];assert len(all_cases)==len({(c['class'],c['name']) for c in all_cases})==3815
bad=lambda r:{(c['class'],c['name']) for g in r['groups'] for c in g['cases'] if c['outcome'] in {'failed','error'}}
oldbad=bad(prior);newbad=bad(full);assert len(oldbad)==118 and len(newbad)==115 and not newbad-oldbad
fixed={'tests/test_phase11_9_synthetic_pilot.py::test_pilot_writes_nothing_to_production_review_directory','tests/unit/test_phase14_benchmark_suite.py::test_benchmark_command_writes_a_complete_unclaiming_report','tests/unit/test_phase14_benchmark_suite.py::test_target_claim_through_the_command_is_not_granted_to_a_dev_machine'}
assert full['totals']==dict(tests=3815,failures=84,errors=31,skipped=0,passed=3700)
anchors=load(R/'docs/generated/master_reaudit/MISSION_29_PROTECTED_DEPENDENCY_EVIDENCE.json');current_cases={(c['class'],c['name']):c for c in all_cases};triage=[]
for group in prior['groups']:
 for c in group['cases']:
  if c['outcome'] not in {'failed','error'}:continue
  _,node=case_node(c,group['files']);now=current_cases[(c['class'],c['name'])];explicit='MISSION22_POLICY' in c['diagnostic'];matches=re.findall(r'MISSION22_POLICY: [^:\n]+: ([^\n]+)',c['diagnostic']);resource=matches[-1].replace(str(R)+'/', '') if matches else anchors.get(node,{}).get('resource_anchor','See captured group policy denials and test source')
  resolved=node in fixed
  assert (now['outcome']=='passed')==resolved
  category='RESOLVED_SYNTHETIC_FIXTURE_COUPLING' if resolved else 'BLOCKED_EXPLICIT_PROTECTED_ACCESS' if 'MISSION22_POLICY' in now['diagnostic'] else 'BLOCKED_INDIRECT_PROTECTED_DEPENDENCY'
  triage.append(dict(test_node=node,Mission39_raw_outcome=c['outcome'],Mission40_raw_outcome=now['outcome'],classification=category,preexisting_baseline='YES',new_regression='NO',reproduced='BEFORE_FIX_AND_FULL_RUN' if resolved else 'FULL_RUN',resource_or_context=resource,evidence_kind='Explicit exception' if explicit else 'Source/previous dependency anchor and captured group policy logs; indirect symptom',disposition='Synthetic fixture corrected without changing runtime or opening live resources' if resolved else 'Dependency unavailable under inherited validation policy; not evidence of physical absence',evidence_group=group['group']))
assert len(triage)==118
with (D/'BASELINE_118_CASE_TRIAGE.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(triage[0]),lineterminator='\n');w.writeheader();w.writerows(triage)
with (S/'TEST_CASE_OUTCOMES.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['test_node','raw_outcome','classification'],lineterminator='\n');w.writeheader()
 for group in full['groups']:
  for c in group['cases']:
   _,node=case_node(c,group['files']);status='BLOCKED_PROTECTED_DEPENDENCY' if (c['class'],c['name']) in newbad else 'PASSED_FIXED_SYNTHETIC_FIXTURE' if node in fixed else 'PASSED';w.writerow(dict(test_node=node,raw_outcome=c['outcome'],classification=status))
commands=[]
for group in full['groups']:
 folder=S/'groups'/group['group'];xml=folder/'pytest.xml.gz';body=gzip.decompress(xml.read_bytes());tree=ET.fromstring(body);duration=sum(float(s.get('time','0')) for s in tree.iter('testsuite'))
 commands.append(dict(group=group['group'],command=group['command'],exit_code=group['exit_code'],tests=group['tests'],failures=group['failures'],errors=group['errors'],skipped=group['skipped'],junit_duration_s=duration,junit_gzip_path=str(xml.relative_to(D)),junit_uncompressed_sha256=hashlib.sha256(body).hexdigest(),artifacts={p.name:sha(p) for p in folder.iterdir() if p.is_file()}))
software=dict(schema='mission40-software-validation/1',full_totals=full['totals'],modules=len(full['all_test_files']),groups=len(full['groups']),junit_duration_s=sum(g['junit_duration_s'] for g in commands),wall_time=load(S/'FULL_RUN_WALL_TIME.json'),blocked_cases=115,blocked_is_subset_of_raw_failures_and_errors=True,baseline_nonpassing=118,resolved_baseline_cases=3,new_regressions=0,triage_counts=dict(collections.Counter(r['classification'] for r in triage)),all_case_ids_unchanged=True,old_and_new_bad_case_difference_exact_three_fixed_cases=True,full_receipt_sha256=sha(S/'FULL_RUN_RECEIPT.json'),commands=commands,whole_repository_acceptance=False,pre_resumption_completed_run_totals=load(S/'COMPLETED_PRE_RESUMPTION_RUN_RECEIPT.json')['totals'],pre_resumption_duration='NOT_RETAINED: temporary JUnit/timing files lost; complete per-case receipt preserved and not added to this final run',focused_final_totals=load(D/'FOCUSED_FIX_VALIDATION_RECEIPT.json')['totals'],earlier_focused_run_duration='NOT_RETAINED; final full run includes the three fixed cases once',intermediate_totals=[load(D/p)['totals'] for p in ['BEFORE_FIX_REPRODUCTION_RECEIPT.json','INTERMEDIATE_FIX_VALIDATION_RECEIPT.json','INTERMEDIATE_FIX_VALIDATION_2_RECEIPT.json','FOCUSED_FIX_VALIDATION_RECEIPT.json']])
(S/'VALIDATION_SUMMARY.json').write_text(json.dumps(software,indent=2)+'\n')
analysis=load(D/'RETAINED_OUTPUT_ANALYSIS_RECEIPT.json');state=load(D/'EXPERIMENT_STATUS_RECONCILIATION.json');reference=load(D/'REFERENCE_RECORD_INSPECTION.json');admission=load(D/'B2_REPLAY_ADMISSION_RECEIPT.json');rows=list(csv.DictReader((D/'PER_EVENT_DESCRIPTIVE_RESULTS.csv').open()));table='\n'.join(f"| {r['event']} | {r['front_sampled_records']} / {r['front_predicted_objects']} | {r['back_sampled_records']} / {r['back_predicted_objects']} | {r['audio_score_ge_frozen_threshold_windows']} / {r['audio_windows']} | {r['B2_frames_with_both_stream_records']} / {r['B2_input_frames']} |" for r in rows)
(D/'REMAINING_METRIC_EVALUATION.md').write_text(f'''# Remaining metric evaluation

Mission40 read and validated saved actual outputs; no original inference or decision replay ran. Thirty per-event raw descriptor rows (six existing descriptor families × five events) were calculated. Ten truth/replay evaluation families remain unavailable. The [metric register](METRIC_EXECUTION_REGISTER.json) records execution, exact numerators/denominators or null with reasons, source references, exclusions, missing observations, censoring and uncertainty for every family.

| Existing event | Front sampled frames / predicted objects | Back sampled frames / predicted objects | Audio score≥0.37 windows / all windows | Both-record B2 inputs / all input frames |
|---|---:|---:|---:|---:|
{table}

These are raw counts, not event-detection rates, accuracy, precision, recall, F1, FP or FN. The rows are the same five physical events, not additional independent samples. Engine and designated control remain separate. Cameras retain independent clocks; front/back counts do not establish relative quality. Audio windows overlap, so no independence assumption or new interval is applied. All13 front/276 back object outputs and120 of423 threshold-crossing audio windows match the existing actual saved results.

B2 input coverage is634 of1079 frames with both stream records;445 have no audio record within the existing causal assembly window. This is not proof of a missing audio source or a reason to pad/interpolate. The existing assembly tolerance0.25s and audio hop0.5s are unchanged. Every original visual PTS and causal integer-sample acoustic timestamp is verified through the saved serialization. [Source/hash checks](RETAINED_OUTPUT_ANALYSIS_RECEIPT.json), [per-event table](PER_EVENT_DESCRIPTIVE_RESULTS.csv).

| Scientific endpoint | Executed? | Numerator / denominator | Exact unavailable dependency |
|---|---|---|---|
| M4 primary / M5 integer companion | No | null / null | Accepted eligible T4/reference and legitimate causal replay/coverage |
| MTR feasibility / lead-in screen | No | null / null | Accepted lead-in/screen/control exposure and actual eligible population |
| T1 / warning correctness | No | null / null | Accepted camera-local T1 plus actual warning/replay outputs |
| Control false alarms / exposure | No | null / null | Accepted control truth/exposure; folder names and model scores are not truth |
| Engine identity/timing correctness | No | null / null | Accepted engine-specific observations; no pooled train endpoint |
| FP/FN, accuracy, precision, recall, F1 | No | null / null | Legitimate matching labels and eligibility |
| Human agreement | No | null / null | Separate original paired observations were not stored; do not reconstruct |
| Boundary censoring / uncertainty | No | null / null | Retained accepted boundary states/values/rationales absent |
| B2 decision-derived summaries | No | null / null | Actual guarded decision replay has not executed |

No sufficient active canonical record was found: the32 inspected reference texts are unchanged, legacy schema6 records stay invalidated, and there is no promotion receipt. Human review remains researcher-reported complete and exact agreement reported; AI references stay separate. No repeat-review request or automatic promotion.

The table retains actual unwindowed audio tail sample counts and last whole-window endpoints in CSV. Those are model-window coverage descriptors, not invented human censoring states. Missing scientific values stay null, not zero; no new inferential method, confidence interval, cutoff, acoustic GT shift, exit or duration padding.
''')
(D/'SOFTWARE_TEST_VALIDATION.md').write_text(f'''# Software validation

Final retained full run: **3815 cases across168 modules/53 groups;3700 passed,84 raw failures,31 raw errors,0 skipped.** The115 nonpassing cases are blocked dependencies under the inherited validation policy and are a subset of raw failures/errors. Full passing acceptance is not claimed. No new regression versus Mission39; three of its118 baseline nonpassing cases are now fixed and passing.

Actual summed JUnit duration: **{software['junit_duration_s']:.3f}s**. End-to-end wall time including orchestration: **{software['wall_time']['elapsed_wall_s']:.3f}s**. [Exact commands/durations/hashes](software_validation/VALIDATION_SUMMARY.json), [full per-case receipt](software_validation/FULL_RUN_RECEIPT.json), [3815 outcomes](software_validation/TEST_CASE_OUTCOMES.csv), retained lossless group JUnit/stdout/stderr/policy logs under software_validation/groups/.

| Run | Passed | Failed | Errors | Skipped | Duration |
|---|---:|---:|---:|---:|---|
| Before-fix exact-three reproduction | 0 | 3 | 0 | 0 | Temporary timing not retained |
| First fixture implementation check | 1 | 2 | 0 | 0 | Temporary timing not retained |
| Corrected fixture schema check | 2 | 1 | 0 | 0 | Temporary timing not retained |
| Final exact-three focused check | 3 | 0 | 0 | 0 | Temporary timing not retained; these cases are also in full run |
| Completed pre-resumption full run | 3700 | 84 | 31 | 0 | Complete per-case receipt survived; temporary timing lost |
| Final retained full run | 3700 | 84 | 31 | 0 | JUnit {software['junit_duration_s']:.3f}s; wall {software['wall_time']['elapsed_wall_s']:.3f}s |

Runs/subsets overlap and are never added. The final full run was repeated because interruption removed temporary timing/reports required by this mission; it saves completed group artifacts incrementally. The earlier completed receipt remains [preserved](software_validation/COMPLETED_PRE_RESUMPTION_RUN_RECEIPT.json), not relabeled incomplete or silently discarded.

Two test modules were corrected: the synthetic pilot no longer assumes27 production files; controlled sentinel bytes are unchanged and actual production opens are refused. Two synthetic benchmark CLI tests use actual generated fixture-file hashes/configs through the existing repository-root argument; they no longer read production weights. Their unversioned fixture is truthfully reported with null revision, while the unchanged real-source environment test still requires a40-character HEAD. Real-artifact fingerprint tests and all assertions on false target/safety claims remain. No production runtime, gate, config, weight, scientific definition or existing real integration test is disabled.

The coarse inventory refresh marks changed tests UNKNOWN/unsafe; it is not an execution grant or automatic safe designation. The final per-case executed evidence is separate. All applicable unit/paired-input/PTS/audio clock/cache/model-config identity/serialization/metrics/human-schema/authorization/refusal/CLI/integration/regression modules were attempted through the inherited guarded runner, no module exclusions. Synthetic outcomes are not railway empirical results; Python hooks are not OS isolation. [Static checks](STATIC_VALIDATION.json) find no new lint issues;20 preexisting pilot-test findings remain, benchmark test has none. Dependency check passes.
''')
counts=software['triage_counts'];(D/'FAILURE_AND_REGRESSION_ANALYSIS.md').write_text(f'''# Failure and regression analysis

All118 Mission39 nonpassing case IDs are reconciled individually in [the triage CSV](BASELINE_118_CASE_TRIAGE.csv), including old/new raw outcomes, reproducibility, resource/context, evidence strength and disposition. The same3815 case IDs ran; no test disappeared and no failing test was disabled.

| Baseline family | Cases | Final disposition |
|---|---:|---|
| Fixable synthetic fixture coupling | 3 | Passed after meaningful fixture corrections |
| Explicit protected-access exception | {counts['BLOCKED_EXPLICIT_PROTECTED_ACCESS']} | Still nonpassing under inherited policy |
| Indirect protected-dependency symptom | {counts['BLOCKED_INDIRECT_PROTECTED_DEPENDENCY']} | Still nonpassing; source/anchor/group policy evidence retained |

Initial reproduction confirms all three repaired cases failed. The intermediate fixtures had two implementation errors: the YAML key was policy_metadata, and the generated artifact tree has no Git revision. Both were corrected and all intermediate receipts retained. These are test-only repairs, not production/scientific fixes. The original hardcoded count did not measure model behavior; synthetic CLI serialization/refusal can be checked with genuine constructed hashes without production weights. The separate actual-artifact tests remain blocked and unchanged.

The remaining115 comprise84 failures and31 setup/test errors. Explicit exception traces identify protected manifests, review corpus/allowlist, model checkpoints, source directories, synchronization evidence or experiment registry access. Indirect cases surface as empty guarded corpora, false readiness, StopIteration or a failed CLI; their resource anchors and fresh group policy logs are identified without claiming an individual explicit denial where one is absent. “Unavailable under this validation policy” does not mean the file is physically missing. No actual protected success, new authority, raw-model/source access or scientific validity is inferred.

No new nonpassing IDs were introduced. No material production-core defect is demonstrated by these failures, so no scientific threshold/gate change or broad engineering rebuild is justified. Earlier Mission39 V3 parity correction stays intact and its8 tests pass in the full run. Current B2 admission is a genuine refusal for absent authorization/promotion, not a reason to bypass a guard.
''')
(D/'SCIENTIFIC_LIMITATIONS.md').write_text('''# Scientific limitations

The pilot is five selected physical events at crossing_A, with ten camera views and front supporting audio. Independent-camera primary analyses remain separate; fusion is exploratory and audio supporting. Correlated sampled frames/windows are not independent events or unique vehicles. Training/development standalone horn recordings are not held-out railway evaluation sources.

B0_front/B0_back/B1 actual inference and B2 input assembly exist. Mission40 reused them without new inference. B2 decision replay remains unexecuted, with zero new decision events/frames; no decision, opening, warning or control-performance outcome is established.634 paired input frames are not634 successful decisions.

Reported human first passes/exact agreement remain positive researcher-reported evidence. Separate original observations were not stored; classmate partial familiarity and post-comparison exposure remain preserved. Legacy reviews stay invalidated; AI proposals are not human GT. No formal accepted canonical fields/promotion are established. Boundary censoring, uncertainty, eligibility, exposure and truth-dependent numerators/denominators remain unavailable, not zero.

Native source PTS and causal audio sample-end serialization are verified on retained derived records, not reauthenticated raw sources or physical camera synchronization. The actual0.25s layer-B input collector and0.5s cache-replay collector are different existing stages; input assembly is not substituted for replay. Unwindowed audio tail is recorded without padding; it does not supply missing human observations. Superseded dB diagnostics are retained and excluded from final predictions.

RD001–055 and27 operation selections remain unchanged, including the27-candidate cohort/two duplicate exclusions. M4 stays primary/M5 integer companion/MTR feasibility. T2/occupancy/RD046 stay deferred, comparator inactive, optional R04 exactly eleven with event_010 excluded. No new hypothesis, inferential test, threshold, training, split, sensor, physical actuation or hardware run.

No safety improvement, accident reduction, universal all-weather/cross-site generalization, real-time/deployment readiness, physical synchronization or fusion superiority claim is supported. Software passing cases demonstrate bounded constructed behavior, not empirical railway performance. The115 blocked software cases prevent whole-repository passing acceptance. This mission does not prepare a professor folder, manuscript or venue package.
''')
(D/'FINAL_RESEARCH_COMPLETION_ASSESSMENT.md').write_text(f'''# Final research completion assessment

**ELIGIBLE_MISSION40_WORK_COMPLETE; B2_DECISION_REPLAY_BLOCKED; ACCEPTED_GT_EVALUATIONS=0; FULL_REPOSITORY_TEST_ACCEPTANCE=NONPASSING.** This completes the requested permitted analysis/testing/reporting work, not the full empirical programme.

| Current direction | Completed scope | Remaining scope |
|---|---|---|
| B0_front | Actual five-front inference and raw descriptors | Accepted-reference evaluation/current exact bindings |
| B0_back | Actual five-back independent inference and raw descriptors | Supported intended clearance/replay binding and accepted reference |
| B1_audio | Actual five-front acoustic inference with corrected trained features | Accepted acoustic truth/eligibility for performance evaluation |
| B2_front | Actual five-event paired inputs,1079 frames | Current descriptive authorization and accepted canonical promotion; no decision replay |
| R04 | Preserved optional definition | Separately adopted exact-eleven branch, not auto-activated |

Three original inference stages and one B2 input stage are complete with limitations; zero complete accepted-GT experiment/evaluation directions are established. No new original-data experiment executes in Mission40. There are156 activity IDs, not156 independent experiments. [Exact status matrix](COMPLETE_EXPERIMENT_STATUS_MATRIX.csv) counts: {json.dumps(state['status_counts'],sort_keys=True)}. Completed support rows are not additional empirical experiments, and historical/deferred rows are not universal pilot requirements.

All valid raw descriptors were computed from actual saved outputs, with exact source/hash references and null scientific endpoints. The current human workflow remains researcher-reported complete; no request to repeat it or reconstruct absent notes. No readiness percentage substitutes for missing scientific evidence.

Before claiming full experimental completion, legitimate accepted source-linked canonical fields/eligibility and promotion, exact current manifest/protocol/metric/config authorization, and actual B2/relevant metric execution are still necessary. The current full software run also retains115 nonpassing protected-context cases, disclosed rather than bypassed. Optional/deferred work and publication/institution/hardware matters are not invented universal prerequisites.
''')
(D/'NEXT_PHASE_RECOMMENDATION.md').write_text('''# Next phase recommendation

Review the genuine retained prediction/input results, exact metric availability and current software triage. No B0/B1 rerun, replacement recording, repeat researcher/classmate pass, new browser or additional broad audit is proposed.

The next B2 execution dependency is concrete: data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json must truthfully bind the actual evaluation manifest, protocol, metric scope, frozen model/config provenance and a legitimate data/governance/stage21_promotion_receipt.json backed by accepted canonical records. The inspected records supply neither. A general instruction to proceed or reported human–AI agreement cannot supply those missing facts. Decide a legitimate recorded-reference/acceptance path before that operation; this mission neither appoints people nor manufactures records or signatures.

Once genuine prerequisites are supplied and independently accepted under the existing protocol, use the saved exact front/audio input manifest for B2 and calculate only the then-eligible per-metric outcomes. Preserve native clocks, independent cameras, engine/control separation and current thresholds. If reference-dependent evaluation is not pursued, describe the current work as inference/input feasibility with explicit unavailable performance endpoints, rather than complete validation.

Any remaining protected integration test needs its particular lawful/resource scope and actual inputs; the inherited guarded run is not such a grant. Do not remove guards or turn known failures into passes. Optional R04 remains separately adopted exactly eleven, event_010 excluded. No full programme expansion, professor evidence folder or manuscript is authorized/prepared here; professor handoff follows researcher review and an accurate claim scope.
''')
(D/'MISSION_40_FINAL_REPORT.md').write_text(f'''# Mission40 final report

Prepared2026-11-08, America/New_York; intake started2026-11-07. **PERMITTED_WORK_COMPLETE; B2_DECISION_REPLAY_NOT_EXECUTED; ACCEPTED_GT_EVALUATIONS=0.** Actual saved inputs were analyzed, three test-fixture defects repaired and the full software programme completed with its remaining nonpassing cases disclosed. No original inference was repeated.

## Direct answers

1. **Did B2 replay execute?** No. The actual real-root CacheOnlyReplayEngine.execute_replay boundary returned AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED before decision processing. [Admission receipt](B2_REPLAY_ADMISSION_RECEIPT.json).
2. **Actual events/frames processed?** Zero original events and zero decision frames in Mission40. Read-only analysis covers five existing physical events/1079 front records/1100 back records/423 acoustic windows and1079 B2 input frames;634 contain both streams. Those are retained inputs, not executed B2 decisions.
3. **Actual B2 results?** No decision outputs. Input coverage remains634 paired/445 without an audio record inside the existing input window. No B2 result file or placeholder is created; refusal metadata is separate.
4. **Metrics calculated?** Thirty per-event raw descriptor rows across six existing families; exact counts/units/source references in [metric register](METRIC_EXECUTION_REGISTER.json) and [table](PER_EVENT_DESCRIPTIVE_RESULTS.csv). Front/back object totals13/276, audio score≥0.37 count120 of423. No correctness interpretation.
5. **GT-blocked metrics?** M4/M5/MTR/T1-warning, truth-based control/engine outcomes, accuracy/precision/recall/F1/FP/FN, agreement and boundary censoring/uncertainty. Null numerators/denominators remain unavailable, not zero. [Metric assessment](REMAINING_METRIC_EVALUATION.md).
6. **Sufficient existing reference?** None found.32 relevant text fingerprints unchanged, zero active unexcused canonical records and no promotion receipt. Legacy invalidations/AI separation remain intact. Reported independent human review/exact agreement remains supporting evidence, not fabricated GT. [Inspection](REFERENCE_RECORD_INSPECTION.json).
7. **The118 historical nonpassing cases?** Three synthetic fixture dependencies are fixed;115 remain blocked under inherited policy. [All118 reconciled](BASELINE_118_CASE_TRIAGE.csv). No case dropped or disabled.
8. **Final test counts?**3815 cases across168 modules/53 groups: **3700 passed,84 failed,31 errors,0 skipped**.115 blocked is the failure/error subset, not an additional count. JUnit {software['junit_duration_s']:.3f}s; wall {software['wall_time']['elapsed_wall_s']:.3f}s. No new regression/full-pass claim. [Validation](SOFTWARE_TEST_VALIDATION.md).
9. **Actual fixes?** Test-only: synthetic pilot checks unchanged sentinels and refuses production opens; two CLI tests use actual constructed artifact hashes/configs instead of production checkpoints. Real-source revision and real-artifact tests remain. No production/scientific algorithm change. [Failure analysis](FAILURE_AND_REGRESSION_ANALYSIS.md).
10. **Complete directions?** Three prior original inference stages complete with limitations; B2 input stage complete. Zero accepted-GT evaluation directions complete. Five current directions are distinct from156 activity rows.
11. **Remaining experiments?** Legitimate reference-dependent B0/B1/B2 evaluations and separately optional R04; historical, retired and unadopted ideas are not automatically required runs. [156-row matrix](COMPLETE_EXPERIMENT_STATUS_MATRIX.csv).
12. **Pilot scientific status?** Five-event single-site descriptive model-output/input feasibility, with no measured safety, accuracy or fusion superiority. Engine/control and cameras remain separate. [Limitations](SCIENTIFIC_LIMITATIONS.md).
13. **Before professor handoff?** Researcher review of genuine results and accurate claim scope; for a fully evaluated claim, actual accepted reference/promotion, current exact descriptive bindings and real remaining evaluations. Keep protected integration limitations visible. No professor/manuscript package prepared. [Completion assessment](FINAL_RESEARCH_COMPLETION_ASSESSMENT.md), [next phase](NEXT_PHASE_RECOMMENDATION.md).

## Evidence and preservation

Started main at c4d65916128dcc12857e4e5b89f98452e118d9c9; origin/main remainsfc3c29a761deaa9e36eca1e5eea4e0205b1f9a74, no push. [Baseline](BASELINE_AND_PRESERVATION.json) pins550 earlier documentary artifacts, verifies209 Mission39 artifact hashes, all seven original researcher hashes and the prior full-run source binding. All prior results and superseded diagnostics remain byte-identical. Only two test modules and the conservative test inventory change; production source/config/schema/gates/models remain unchanged. New result artifacts are solely saved-output analysis/metadata/software evidence, never raw videos/audio, new predictions or new GT.

The earlier completed3700/84/31/0 full receipt survived interruption; temporary timing/JUnit files did not. It is preserved separately and not added to final totals. A final identical-code full run retained each completed group's real JUnit/stdout/stderr/policy evidence incrementally. Intermediate failed fixture checks also remain, including the wrong YAML fixture key and expected null Git metadata correction. Actual commands/counts/timings are recorded without inventing missing older durations.

All human-review flags remain as researcher supplied: five front passes reportedly complete, exact agreement reported, separate originals stored=0; classmate partial familiarity retained, accepted canonical GT not established. No repeat-review request, signature, people qualification, boundary or note reconstruction. No promotion or authorization is fabricated. Missing actual binding paths are explicit, and no real-data replay is placed in a synthetic root or routed around the gate.

RD001–055/27 selections, five-event pilot/27-candidate cohort/two duplicates, independent-camera primary, exploratory fusion/supporting audio, M4 primary/M5 integer companion/MTR feasibility, current model/thresholds, metric-specific denominators and clock/censoring rules remain. Physical T2/occupancy/RD046 and comparator remain deferred/inactive. R04 stays optional exact-eleven with event_010 excluded. No new training/CV/split/sensor/hardware/actuation/inferential test, acoustic GT shift, invented exit, duration padding, external contact, raw release or professor/publication work.

Only exact Mission40 deliverables and justified test/inventory paths are staged and committed locally after delivery checks. Seven original researcher changes and private runtime caches remain unstaged; no broad staging/reset/clean/amend/rebase/history rewrite/push. The containing commit hash and final worktree are checked and reported after commit.
''')
# Improve spacing in prose without touching IDs, hashes, paths or machine-readable data.
for p in D.glob('*.md'):
 s=p.read_text()
 for a,b in {'Prepared2026':'Prepared 2026','started2026':'started 2026','across168':'across 168','all118':'all 118','All118':'All 118','threeof':'three of','in156':'in 156','The115':'The 115','The118':'The 118','All13':'All 13','the32':'the 32','remainsfc3':'remains fc3'}.items():s=s.replace(a,b)
 p.write_text(s)
os.environ['MPLCONFIGDIR']=tempfile.mkdtemp(prefix='m40_figures_',dir='/private/tmp')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(7,3.5));vals=[3700,115];bars=ax.bar(['Passed cases','Remaining protected dependencies'],vals,color=['#23675e','#a97734'])
for bar,n in zip(bars,vals):ax.text(bar.get_x()+bar.get_width()/2,n+35,str(n),ha='center')
ax.set_ylim(0,4300);ax.set_ylabel('Unique software cases');ax.set_title('Mission40 software validation — not model performance');ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(S/'SOFTWARE_OUTCOMES.png',dpi=170);plt.close(fig)
print(json.dumps(dict(totals=full['totals'],triage=counts,JUnit_seconds=software['junit_duration_s'],wall_seconds=software['wall_time']['elapsed_wall_s'],required_nonconditional_deliverables=8,B2_result_file_absent=not (D/'B2_FRONT_DECISION_REPLAY_RESULTS.md').exists())))
