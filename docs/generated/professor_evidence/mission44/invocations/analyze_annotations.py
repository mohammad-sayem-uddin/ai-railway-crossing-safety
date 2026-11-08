"""Deep capability inspection of every adopted original annotation; no inferred labels."""
from common import *
from collections import Counter
entries=[];ledger={};keyrows=[];dups=[]
def walk(x,path=''):
 if isinstance(x,dict):
  for k,v in x.items():
   p=path+'.'+k if path else k;yield p,k,v;yield from walk(v,p)
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+f'[{i}]')
def hook(pairs):
 d={}
 for k,v in pairs:
  if k in d:dups.append(k)
  d[k]=v
 return d
for event,e in INV.items():
 p=R/e['active_proposal_file'];before=len(dups);x=json.loads(p.read_text(),object_pairs_hook=hook);ledger[str(p.relative_to(R))]=sha(p);nodes=list(walk(x));ts=x.get('proposed_timestamps',{});md=x.get('proposed_train_metadata',{});media=x.get('ai_assistant_metadata',{}).get('input_media_files',[]);declared={q.get('sha256')for q in media}
 bbox=[(path,v)for path,k,v in nodes if k.lower()in ['bbox','bbox_xyxy','bounding_box','bounding_boxes','boxes','xmin','xmax','x_min','x_max']and v is not None]
 frame_refs=[(name,t.get('reference_camera'),t.get('frame_index'))for name,t in ts.items()if isinstance(t,dict)and t.get('frame_index')is not None]
 rows={'event':event,'cohort':e['cohort'],'annotation_file':str(p.relative_to(R)),'annotation_sha256':sha(p),'schema':x.get('schema_version'),'researcher_adopted':True,'provenance':'Existing AI-assisted content, reported manually verified and explicitly adopted; separate manual observations not stored','duplicate_JSON_keys':len(dups)-before,'frame_bbox_records':len(bbox),'fully_box_annotated_frames':0,'object_class_reference_coverage':'No per-box object class IDs; event train type/direction are metadata, not front/rear/side box labels','boundary_frame_references':len(frame_refs),'explicit_native_PTS_annotation_fields':sum(k.lower()in ['pts','pts_ticks','timebase','time_base']for path,k,v in nodes),'boundary_values_seconds':sum(isinstance(t,dict)and isinstance(t.get('value_s'),(int,float))for t in ts.values()),'event_train_present':md.get('train_present'),'event_horn_status':md.get('horn_status'),'horn_onset_s':md.get('horn_onset_s'),'horn_offset_s':md.get('horn_offset_s'),'explicit_audio_window_label_records':0,'boundary_visibility_observability_flags':sum(k=='candidate_observable'for path,k,v in nodes),'boundary_ambiguity_flags':sum(k=='ambiguity_flag'for path,k,v in nodes),'horn_uncertainty_s':md.get('horn_uncertainty_s'),'qualitative_confidence_note_present':bool(md.get('confidence_note')),'formal_per_object_occlusion_labels':0,'both_source_hashes_match':all(e['raw_media'][role]['sha256']in declared for role in ['front','back']),'boundary_camera_binding':'Camera/FPS/frame references where explicitly supplied; not a full native-PTS frame-label dataset','horn_camera_binding':'Event references both members; horn field lacks independent member-specific binding','valid_use':'Adopted event-label comparison at existing declared scope; candidate-boundary/source diagnostics; no box/window or canonical timing accuracy','canonical_GT':'NOT_ESTABLISHED'}
 entries.append(rows)
 for path,k,value in nodes:
  if any(t in k.lower()for t in ['bbox','class','frame','pts','time','horn','visible','observ','occlu','uncert','ambigu','confidence']):keyrows.append({'event':event,'field_path':path,'value_type':type(value).__name__,'value':json.dumps(value,separators=(',',':')),'source_sha256':sha(p),'scope':'Literal adopted annotation field; no new label inferred'})
 assert not bbox,'Existing boxes discovered: inspect before declaring unavailable'
table('ANNOTATION_CAPABILITY_MATRIX.csv',entries);table('ANNOTATION_FIELD_STRUCTURE.csv',keyrows)
summary={'schema':'mission44-deep-annotation-capabilities/1','events':27,'paired_hash_alignment_events':sum(e['both_source_hashes_match']for e in entries),'schema_counts':dict(Counter(e['schema']for e in entries)),'events_with_boxes':0,'frames_with_box_reference':0,'events_with_event_train_label':sum(e['event_train_present']is not None for e in entries),'events_with_explicit_horn_status':sum(e['event_horn_status']is not None for e in entries),'events_with_horn_onset':sum(e['horn_onset_s']is not None for e in entries),'events_with_horn_offset':0,'audio_windows_with_reference_labels':0,'events_with_boundary_frame_refs':sum(e['boundary_frame_references']>0 for e in entries),'boundary_frame_references':sum(e['boundary_frame_references']for e in entries),'native_PTS_annotation_fields':sum(e['explicit_native_PTS_annotation_fields']for e in entries),'formal_object_occlusion_reference_records':0,'duplicate_JSON_keys':dups,'annotation_sha256':ledger,'AI_assisted_reference_adoption_preserved':True,'M43_capability_claims_confirmed_without_invented_labels':True};save(D/'ANNOTATION_CAPABILITY_SUMMARY.json',summary);print(json.dumps({k:v for k,v in summary.items()if k!='annotation_sha256'},indent=2))
