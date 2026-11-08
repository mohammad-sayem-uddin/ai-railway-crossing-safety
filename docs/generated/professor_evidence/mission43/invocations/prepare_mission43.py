"""Preserve the delivered state before full-cohort execution; metadata/source reads only."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'docs/generated/professor_evidence/mission43'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def g(*a):return subprocess.check_output(['git',*a],text=True).strip()
past=R/'docs/generated/professor_evidence/mission42';b=json.loads((past/'10_REPRODUCIBILITY/BASELINE_AND_PRESERVATION.json').read_text());pins=b['prior_artifact_sha256'].copy()
for p in past.rglob('*'):
 if p.is_file():pins[str(p.relative_to(R))]=h(p)
for s,v in pins.items():assert h(R/s)==v,s
for s,v in b['original_seven_researcher_sha256'].items():assert h(R/s)==v,s
reports={}
for n in range(29,43):
 p=R/('docs/generated/master_reaudit'if n<39 else'docs/generated/research_results')/f'mission{n}'
 if n==29:p=R/'docs/generated/master_reaudit'
 if n==42:p=past
 matches=list(p.glob(f'MISSION_{n}*REPORT.md'))if n!=42 else[p/'PROFESSOR_PACKAGE_COMPLETION_REPORT.md']
 if n==29:matches=list(p.glob('MISSION_29_FINAL*.md'))+list(p.glob('MISSION_29_FINAL_VALIDATION.json'))
 for f in matches:
  text=f.read_text();reports[str(f.relative_to(R))]=dict(sha256=h(f),characters=len(text),opening=text[:650])
source={}
for key in ['modules','shared_source_sha256']:
 source.update(b['maintained_source_bindings'][key])
for s,v in source.items():assert h(R/s)==v,s
annotations={str(p.relative_to(R)):h(p)for p in (R/'data/ground_truth').rglob('*')if p.is_file()and p.suffix in {'.json','.md','.csv','.jsonl'}}
x=dict(schema='mission43-baseline/1',starting_commit=g('rev-parse','HEAD'),tracking=g('rev-parse','origin/main'),initial_status=g('status','--short'),prior_artifact_sha256=pins,original_seven_researcher_sha256=b['original_seven_researcher_sha256'],source_sha256=source,annotation_text_sha256=annotations,read_historical_reports=reports,request_sha256=h(Path('/Users/sayemuddin/.codex/attachments/5ea89733-a3d7-4030-99de-5c8bf56eacb5/Pasted text.txt')),request_statement='The user now confirms that the 27-event dataset annotations have been manually verified.',request_statement_scope='Genuine new researcher report; individual field/annotation linkage and accepted reference status must be inspected, never fabricated.')
(D/'BASELINE_AND_PRESERVATION.json').write_text(json.dumps(x,indent=2)+'\n');print('Prior pins',len(pins),'annotation text records',len(annotations),'source bindings',len(source),'baseline',x['starting_commit'])
