"""Current evidence index and executive handoff, preserving executed scope documents."""
from common import *
import csv
r=read(D/'ACTUAL_FULL_COHORT_RESULTS.json');v=read(D/'ACTUAL_VISUAL_RUN_MANIFEST.json');a=read(D/'ACTUAL_AUDIO_RUN_MANIFEST.json')
(D/'EXECUTIVE_RESEARCH_SUMMARY.md').write_text('''# Full27-event executive research summary

The project examined the existing image and supporting horn models on23 train events,3 no-train controls and1 engine-only case, front/back each, at the existing site. All54 current source hashes match the established inventory. The earlier five-event model outputs are reused once; the remaining22 events were genuinely processed with the frozen models/configuration.

Front vision produced6613 sampled records and329 objects; back vision6479 records and1020 objects. Corrected natural-log V3 inference produced2600 acoustic windows and445 model-positive windows at0.37 across27 front tracks. Those repeated outputs are not independent physical events or accuracy estimates.

The researcher explicitly approved the existing AI-assisted annotations as final after reporting manual verification, without separate manual notes. That genuine approval is bound to27 active versions/hashes. An explicitly scoped exploratory event-label comparison uses the existing max-window acoustic recording rule: among23 train events with explicit horn labels (13 present,10 absent_observed), TP12/FP10/FN1/TN0;precision54.55%,recall92.31%,F10.6857,specificity0%,ROC-AUC0.6846,AP0.7739. All10 adopted horn-absent train cases trigger, revealing poor specificity relative to these labels. The engine is separate and controls' null horn labels are excluded.

The comparison is limited by AI-assisted reference provenance, absent separate observations and horn fields that identify the paired event rather than an independently verified front acoustic member. It is not window/timing accuracy or independent-human-GT validation. Missing frame boxes prevent image AP/mAP and matched detection correctness. No labels, windows or human records were invented.

All27 B2 input assemblies are complete:6614 query frames,3897 with both stream records,2717 without audio in the input window. Actual B2 decisions remain unexecuted: the existing guard refuses admission because genuine canonical promotion/protocol bindings are absent. Researcher content approval does not fabricate those records or canonical Stage2.1 acceptance.

Fresh full guarded software testing executed3815 cases:3700 passed,84 failed,31 errors,0 skipped, with the same115 nonpassing cases as Mission40. Separately,15 existing actual-metadata integration cases pass with unchanged tests and production guards; overlapping contexts are not added together. No new core defect, training, threshold change, model replacement or split was introduced.

The evidence supports these bounded full-cohort output/error and adopted-label findings. It does not establish generalization, safety benefit, deployment readiness, full B2 completion or a fully passing repository. The professor should review [the findings](MISSION_43_FINAL_REPORT.md), [reference scope](ANNOTATION_AND_REFERENCE_VERIFICATION.md), [metrics](QUANTITATIVE_METRICS_AND_SCOPE.md) and [remaining exact dependencies](LIMITATIONS_AND_NEXT_RESEARCH.md) before deciding stronger claims or further research.
''')
(D/'README.md').write_text('# Mission43 professor evidence\n\nStart with the [executive research summary](EXECUTIVE_RESEARCH_SUMMARY.md) and [professor guide](README_FOR_PROFESSOR.md).\n\n[Final report](MISSION_43_FINAL_REPORT.md), [27-event matrix](FULL_27_EVENT_COVERAGE_MATRIX.csv), [acceptance status](FINAL_ACCEPTANCE_STATUS.json), [evidence manifest](EVIDENCE_MANIFEST.csv).\n\nRun `python3 verify_package.py` here to verify packaged evidence only. Original-data inference is complete at the existing27-event visual/front-acoustic scope; unsupported box/window/canonical-timing evaluations and B2 decisions remain explicitly unavailable.\n')
entries=[]
for role in ['front','back']:
 entries.append(dict(experiment_id=v['run_id']+'/B0_'+role,actual_parent_run_id=v['run_id'],stage='ORIGINAL_VISION_INFERENCE',event_count=27,member_count=27,new_original_members=22,reused_members=5,status='COMPLETE_ORIGINAL_INFERENCE; reference-box evaluation unavailable',manifest='ACTUAL_VISUAL_RUN_MANIFEST.json',manifest_sha256=sha(D/'ACTUAL_VISUAL_RUN_MANIFEST.json'),metrics='VISUAL_PER_EVENT_RESULTS.csv; descriptors, not box correctness'))
entries.append(dict(experiment_id=a['run_id']+'/B1_front_audio',actual_parent_run_id=a['run_id'],stage='ORIGINAL_FRONT_AUDIO_INFERENCE',event_count=27,member_count=27,new_original_members=22,reused_members=5,status='COMPLETE_ORIGINAL_INFERENCE; scoped23-event adopted-label comparison executed',manifest='ACTUAL_AUDIO_RUN_MANIFEST.json',manifest_sha256=sha(D/'ACTUAL_AUDIO_RUN_MANIFEST.json'),metrics='AUDIO_ADOPTED_EVENT_LABEL_METRICS.json; exploratory event-label agreement'))
entries.append(dict(experiment_id=a['run_id']+'/B2_input_assembly',actual_parent_run_id=a['run_id'],stage='INPUT_ASSEMBLY_ONLY',event_count=27,member_count=27,new_original_members=22,reused_members=5,status='INPUTS_COMPLETE; NO_DECISION_REPLAY',manifest='ACTUAL_AUDIO_RUN_MANIFEST.json',manifest_sha256=sha(D/'ACTUAL_AUDIO_RUN_MANIFEST.json'),metrics='B2_INPUT_COVERAGE.csv; no decision metrics'))
with(D/'EXPERIMENT_INDEX.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(entries[0]),lineterminator='\n');w.writeheader();w.writerows(entries)
save(D/'EXPERIMENT_INDEX_SCOPE.json',{'identifier_basis':'Section identifiers derive from actual recorded run IDs plus named existing conditions; assigned for navigation, not extra executions or fabricated start times','exact_scientific_experiment_run_ids':[v['run_id'],a['run_id']],'all_genuinely_executable_current_work_done':True,'entire_research_programme_complete':False,'no_extra_physical_events_inferred':True})
# Record frozen-binding restoration after formatting; no inference/metric recomputation needed.
mediahash=sha(D/'EXECUTION_SCOPE.md');evalhash=sha(D/'EVALUATION_SCOPE_FREEZE.md');assert evalhash==read(D/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json')['scope_sha256']
for phase in ['verification','vision','audio']:
 for state in ['ISSUED','CLOSED']:
  p=D/'operations'/f'{phase}_{state}_AUTHORIZATION.json';x=read(p);assert x['bindings']['protocol_document']['sha256']==mediahash
  digest=hashlib.sha256(json.dumps({k:v for k,v in x.items()if k!='record_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest();assert digest==x['record_sha256']
for name,manifest in [('verify_sources.py',read(D/'SOURCE_VERIFICATION_RECEIPT.json')),('run_vision.py',v),('run_audio.py',a)]:
 assert sha(D/'invocations'/name)==manifest['invocation_sha256'],name
save(D/'EXECUTED_SCOPE_BINDING_VALIDATION.json',{'schema':'mission43-executed-scope-binding-validation/1','valid':True,'media_scope_sha256':mediahash,'evaluation_scope_sha256':evalhash,'three_actual_invocation_hashes_match':True,'six_issued_closed_record_seals_match':True,'canonical_media_slot_absent':not(R/'data/governance/AUTH-MEDIA-ACCESS.json').exists(),'formatting_correction':'A final formatting pass temporarily touched the two new hash-bound scope Markdown files. Their exact executed bytes were restored and verified against original recorded SHA256; no authorization, original prediction, metric input or prior evidence was changed. Frozen scopes are excluded from further polishing.'})
print('Executive summary, actual-run index and all executed scope/invocation seals checked.')
