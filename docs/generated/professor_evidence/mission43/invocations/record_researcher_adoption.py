"""Record the actual new researcher approval without editing or promoting originals."""
from pathlib import Path
from datetime import datetime,UTC
import json,hashlib,csv
R=Path.cwd();D=R/'docs/generated/professor_evidence/mission43';p=D/'ANNOTATION_RECORD_INSPECTION.json';x=json.loads(p.read_text())
statement='I have verifed all ai annotation all are approved same it is thats why I did not store my manual ones you can take the Ai annotation as the final'
a={'schema':'mission43-researcher-annotation-adoption/1','statement':statement,'origin':'Actual researcher reply in current Mission43 conversation to exact existing annotation path/version question','recorded_at_utc':datetime.now(UTC).isoformat(),'recorded_by':'Codex agent transcription; unsigned researcher statement','authority_attribution':'Existing researcher authority binding preserved; no identity or signature invented','decision':'RESEARCHER_APPROVES_AI_ASSISTED_ANNOTATIONS_AS_FINAL_REFERENCE_CONTENT','separate_manual_observations_stored':False,'identity_selection':'Existing active proposal per docs/PHASE11_3_REVIEW_INVENTORY.json, all27; historical superseded versions preserved separately, never merged','limitations':['Researcher adoption is genuine evidence and not dismissed as no approval','Not independent newly stored human observations or inter-rater evidence','Does not itself create missing frame boxes, acoustic window labels, boundary states/clock proofs or canonical promotion','Legacy review invalidations remain intact; active AI-assisted references and formal canonical GT remain separate'],'adopted_active_annotations':[]}
for e in x['events']:
 e.update(researcher_approval_received=True,manual_report_to_exact_version='RESEARCHER_ADOPTION_OF_EXISTING_ACTIVE_PROPOSAL; all AI annotations approved in current reply',reference_content_status='RESEARCHER_ADOPTED_AI_ASSISTED_REFERENCE',canonical_status='NOT_ESTABLISHED; candidate schema and missing canonical boundary/assignment/acceptance evidence')
 a['adopted_active_annotations'].append({k:e[k]for k in ['event','active_proposal_path','active_proposal_sha256','active_proposal_schema','active_proposal_both_source_hashes_match']})
x['new_researcher_adoption_record']='RESEARCHER_ANNOTATION_ADOPTION.json';x['scope']='Actual active candidate content now adopted by researcher, with no separate notes; technical/canonical eligibility assessed independently. Legacy records remain invalidated; no new timestamps, values or fake human files.'
(D/'RESEARCHER_ANNOTATION_ADOPTION.json').write_text(json.dumps(a,indent=2)+'\n');p.write_text(json.dumps(x,indent=2)+'\n')
with(D/'ANNOTATION_COVERAGE_MATRIX.csv').open(newline='')as f:rows=list(csv.DictReader(f));fields=list(rows[0])+['researcher_approval_received','reference_content_status']
for row in rows:row.update(manual_report_to_exact_version='RESEARCHER_ADOPTS_CURRENT_ACTIVE_PROPOSAL',researcher_approval_received=True,reference_content_status='RESEARCHER_ADOPTED_AI_ASSISTED_REFERENCE; not independent human observations')
with(D/'ANNOTATION_COVERAGE_MATRIX.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
print('Recorded genuine adoption of27 active version/hash references; preserved originals and canonical distinction.')
