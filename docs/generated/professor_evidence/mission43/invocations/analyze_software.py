"""Reconcile current full retained software execution against all historical case outcomes."""
from common import *
import csv,collections,gzip,xml.etree.ElementTree as ET
old=read(R/'docs/generated/research_results/mission40/software_validation/FULL_RUN_RECEIPT.json');new=read(D/'software_validation/FULL_RUN_RECEIPT.json')
def cases(x):return {(c['class'],c['name']):(g['group'],c)for g in x['groups']for c in g['cases']}
a=cases(old);b=cases(new);assert len(a)==len(b)==3815 and set(a)==set(b)
changes=[{'class':k[0],'name':k[1],'before':a[k][1]['outcome'],'now':b[k][1]['outcome']}for k in a if a[k][1]['outcome']!=b[k][1]['outcome']]
assert not changes,changes
rows=[];outcomes=[];explicit=0
for k,(group,c)in b.items():
 module=next(f for f in new['groups'][[g['group']for g in new['groups']].index(group)]['files'] if c['class'].startswith(f[:-3].replace('/','.')))
 node=module+('::'+c['class'][len(module[:-3].replace('/','.'))+1:].replace('.','::') if c['class']!=module[:-3].replace('/','.') else '')+'::'+c['name'];outcomes.append({'test_node':node,'class':k[0],'name':k[1],'outcome':c['outcome'],'group':group})
 if c['outcome']in ['failed','error']:
  direct='MISSION22_POLICY:'in c['diagnostic'];explicit+=direct
  rows.append(dict(test_node=node,outcome=c['outcome'],group=group,classification='INHERITED_EXPLICIT_PROTECTED_DEPENDENCY'if direct else'INHERITED_INDIRECT_PROTECTED_CORPUS_OR_READINESS_CONTEXT',new_regression=False,previous_M40_outcome=a[k][1]['outcome'],evidence='software_validation/groups/'+group+'/pytest.xml.gz',diagnostic=c['diagnostic'],disposition='No new code defect demonstrated; existing resource-free audit policy intentionally denies protected production dependencies. Do not weaken guard/test or manufacture missing reference.'))
for name,data in [('CURRENT_TEST_CASE_OUTCOMES.csv',outcomes),('CURRENT_NONPASSING_TEST_TRIAGE.csv',rows)]:
 with(D/'software_validation'/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
# Verify actual group files, not just receipt counters.
cts=collections.Counter();ids=[]
for p in(D/'software_validation/groups').glob('*/pytest.xml.gz'):
 for c in ET.fromstring(gzip.decompress(p.read_bytes())).iter('testcase'):
  ids.append((c.get('classname'),c.get('name')));cts['errors'if c.find('error')is not None else'failures'if c.find('failure')is not None else'skipped'if c.find('skipped')is not None else'passed']+=1
assert len(ids)==3815 and len(set(ids))==3815
summary={'schema':'mission43-current-full-validation-reconciliation/1','current_full_run_executed':True,'initial_and_final_counts':new['totals'],'same_code_no_fix_second_rerun_needed':True,'actual_JUnit_outcomes':dict(cts),'all3815_case_ids_preserved':True,'outcome_changes_from_M40':changes,'nonpassing':len(rows),'explicit_protected_exceptions':explicit,'indirect_protected_context':len(rows)-explicit,'new_material_software_defects_demonstrated':0,'tests_modified_or_disabled':0,'source_bindings_unchanged':new['source_bindings_unchanged'],'not_executed':new['not_executed'],'whole_repository_full_pass':False,'policy':'Complete inherited guarded audit programme, not unrestricted protected-data acceptance; no synthetic fixture counted as an original experiment'}
save(D/'software_validation/CURRENT_VALIDATION_SUMMARY.json',summary);print(json.dumps({k:v for k,v in summary.items()if k not in ['policy']},indent=2))
