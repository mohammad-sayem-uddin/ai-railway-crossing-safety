"""Case/condition and integration-context analysis of actual saved results."""
from common import *
import csv,collections,xml.etree.ElementTree as ET

def table(n,data):
 with(D/n).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
def load(n):return list(csv.DictReader((D/n).open()))
comp=load('AUDIO_ADOPTED_EVENT_COMPARISONS.csv');a={e['event']:e for e in read(D/'ACTUAL_AUDIO_RUN_MANIFEST.json')['events']};out=[]
for e in comp:
 if e['agreement_class']not in ['FP','FN']:continue
 source=a[e['event']];p=R/source['predictions']['path'];assert sha(p)==source['predictions']['sha256'];r=[json.loads(t)for t in p.read_text().splitlines()];maximum=max(r,key=lambda x:x['metadata']['probability']);positive=[x for x in r if x['metadata']['probability']>=.37]
 out.append(dict(event=e['event'],comparison_class=e['agreement_class'],adopted_event_horn_label=e['adopted_event_horn_label'],max_model_score=maximum['metadata']['probability'],max_score_window_start_s=maximum['metadata']['window_start_s'],max_score_window_end_s=maximum['timestamp_s'],native_causal_end_fraction=json.dumps(maximum['metadata']['causal_end_fraction']),first_positive_window_end_s=positive[0]['timestamp_s']if positive else None,positive_windows=len(positive),all_windows=len(r),annotation_file=e['annotation_file'],annotation_sha256=e['annotation_sha256'],prediction_file=source['predictions']['path'],interpretation='Actual review cue for event-label mismatch; max-score window is not a new localized truth/false-alarm annotation'))
table('AUDIO_ERROR_REVIEW_WINDOWS.csv',out)
conditions=collections.defaultdict(list)
for e in load('VISUAL_PER_EVENT_RESULTS.csv'):conditions[e['camera'],e['adopted_lighting']or'UNKNOWN',e['adopted_weather']or'UNKNOWN'].append(e)
data=[]
for(role,light,weather),r in sorted(conditions.items()):data.append(dict(camera=role,adopted_lighting=light,adopted_weather=weather,physical_events=len(r),sampled_records=sum(int(e['sampled_records'])for e in r),predicted_objects=sum(int(e['predicted_objects'])for e in r),interpretation='Output descriptors by researcher-adopted AI condition metadata; no condition accuracy or fresh weather/lighting verification'))
table('OUTPUTS_BY_ADOPTED_CONDITION.csv',data)
# Keep audit and authorized read-only follow-up contexts separate, without changing cases/guards.
p=D/'software_validation/CURRENT_NONPASSING_TEST_TRIAGE.csv';rows=list(csv.DictReader(p.open()));tree=ET.parse(D/'software_validation/READ_ONLY_DATA_INTEGRATION.xml');follow={(e.get('classname'),e.get('name')):'failed'if e.find('failure')is not None else'error'if e.find('error')is not None else'skipped'if e.find('skipped')is not None else'passed'for e in tree.iter('testcase')};assert len(follow)==15 and set(follow.values())=={'passed'}
allcases={(c['class'],c['name']):c for g in read(D/'software_validation/FULL_RUN_RECEIPT.json')['groups']for c in g['cases']};assert set(follow)<=set(allcases)and all(allcases[k]['outcome']in ['failed','error']for k in follow)
for row in rows:
 # Resolve actual node from the unchanged test source module and class in full receipt.
 matched=[(k,c)for k,c in allcases.items()if k in follow and row['test_node'].endswith('::'+k[1])and row['test_node'].split('::')[0][:-3].replace('/','.')==k[0].split('.Test')[0]]
 row['authorized_readonly_metadata_followup']='passed'if matched else'NOT_REEXECUTED_IN_THIS_CONTEXT';row['contexts_not_added']='Same existing cases; full guarded audit counts stay3815/3700/84/31/0'
with p.open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
s=read(D/'software_validation/CURRENT_VALIDATION_SUMMARY.json');s.update(additional_normal_readonly_integration=dict(tests=15,passed=15,failures=0,errors=0,skipped=0,original_records_unchanged=True,same_fifteen_cases_were_guarded_audit_nonpasses=True,not_added_to3815_total=True),guarded_nonpasses_without_separate_passing_current_context=100,meaning='115 remain nonpassing in the full resource-free audit;15 also pass unchanged in separately authorized actual-metadata context. No universal full-pass claim.')
save(D/'software_validation/CURRENT_VALIDATION_SUMMARY.json',s)
print('Case/condition tables and15-case follow-up contexts retained.')
