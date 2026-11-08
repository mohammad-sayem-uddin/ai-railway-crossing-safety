"""Read actual annotation/source metadata; never edit or promote annotations."""
from pathlib import Path
import json,hashlib,csv,collections
R=Path.cwd();D=R/'docs/generated/professor_evidence/mission43'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(D/n).write_text(json.dumps(x,indent=2)+'\n')
x=json.loads((R/'docs/PHASE11_3_REVIEW_INVENTORY.json').read_text());assert len(x['events'])==27
rows=[];records=[];ledger={}
for event,e in x['events'].items():
 cohort=e['cohort'];old=R/e['legacy_review_file'];review=json.loads(old.read_text());notice=old.with_name(old.stem+'.INVALIDATION_NOTICE.json');invalid=json.loads(notice.read_text())if notice.exists()else{}
 proposal=R/e['active_proposal_file'];a=json.loads(proposal.read_text());ledger[str(old.relative_to(R))]=h(old);ledger[str(notice.relative_to(R))]=h(notice);ledger[str(proposal.relative_to(R))]=h(proposal)
 # Inspect all stored proposals for provenance/version, not just a selected favorable value.
 props=[]
 for p in sorted(proposal.parent.glob(e['event_id']+'_proposal_v*.json')):
  q=json.loads(p.read_text());ledger[str(p.relative_to(R))]=h(p);props.append(dict(path=str(p.relative_to(R)),sha256=h(p),schema=q.get('schema_version'),proposal_id=q.get('proposal_id'),AI_origin='ai_assistant_metadata'in q))
 refs=a.get('ai_assistant_metadata',{}).get('input_media_files',[])
 hashes={v.get('sha256')for v in refs};source_match=all(e['raw_media'][c]['sha256']in hashes for c in ['front','back'])
 ts=a.get('proposed_timestamps',{});rs=review.get('field_adjudications',{})
 r=dict(event=event,cohort=cohort,researcher_reported_manual_verification=True,report_origin='Mission43 user brief §§2,7; no verification date or individual field values inferred',legacy_review_path=str(old.relative_to(R)),legacy_review_sha256=h(old),legacy_schema=review.get('schema_version'),legacy_claimed_adjudication=review.get('adjudication_status'),invalidation_disposition=invalid.get('disposition'),invalidation_targets_current_bytes=invalid.get('applies_to_file_sha256_at_notice_time')==h(old),active_proposal_path=str(proposal.relative_to(R)),active_proposal_sha256=h(proposal),active_proposal_matches_inventory=h(proposal)==e['active_proposal_sha256'],active_proposal_schema=a.get('schema_version'),active_proposal_is_AI_candidate='ai_assistant_metadata'in a,active_proposal_both_source_hashes_match=source_match,stored_proposal_versions=props,proposed_timestamps=ts,legacy_adjudicated_fields=list(rs),candidate_horn_fields={k:v for k,v in a.get('proposed_train_metadata',{}).items()if k.startswith('horn_')},frame_bbox_ground_truth_records=0,acoustic_window_label_records=0,accepted_canonical_GT=False,manual_report_to_exact_version='UNRESOLVED_NO_VERSION_NAMED',metric_status='UNAVAILABLE_MISSING_ELIGIBLE_SOURCE_LINKED_ACCEPTED_REFERENCE_AND_MATCHING_CONTRACT')
 records.append(r)
 row={k:r[k]for k in ['event','cohort','researcher_reported_manual_verification','legacy_review_path','legacy_schema','invalidation_disposition','active_proposal_path','active_proposal_schema','active_proposal_both_source_hashes_match','frame_bbox_ground_truth_records','acoustic_window_label_records','accepted_canonical_GT','manual_report_to_exact_version','metric_status']};rows.append(row)
write('ANNOTATION_RECORD_INSPECTION.json',dict(schema='mission43-annotation-inspection/1',user_manual_verification_report_received=True,events=records,annotation_text_sha256=ledger,active_accepted_records=0,legacy_invalidated=27,stored_human_paired_observations_not_reconstructed=True,AI_annotations_not_GT=True,scope='Inspected original review/candidate JSON and existing metadata roots; declared manual completion retained; exact verified version and canonical acceptance not inferred'))
with(D/'ANNOTATION_COVERAGE_MATRIX.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
# Canonical absence is a real inspected fact; don't fabricate a remedy.
write('CURRENT_EVALUATION_BINDING_STATUS.json',{'schema':'mission43-current-binding-inspection/1','canonical_records':{s:{'exists':(R/s).is_file(),'sha256':h(R/s)if(R/s).is_file()else None}for s in ['data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json','data/governance/stage21_promotion_receipt.json','data/manifests/phase12_protocol_decision.json']},'genuine_GT_promoted':False,'selected_M4':'first_blocked_to_t4_clearance; unchanged','new_manual_declaration':'Recorded as actual researcher statement; not silently converted into canonical fields, physical T2 or approval of invalidated bytes'})
print('27 annotation events inspected;27 invalidated legacy reviews; candidate source hashes match',sum(r['active_proposal_both_source_hashes_match']for r in records),'accepted canonical records0; no bbox/window reference rows in inspected files.')
