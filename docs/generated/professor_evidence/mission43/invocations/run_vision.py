"""Run only the44 unprocessed camera members; reuse ten byte-bound actual prior outputs."""
from common import *
import time,traceback,resource,importlib.metadata as md
from railway_detection.safety.media_guard import require_media_authorization
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor,serialize_front_visual_record,serialize_evidence_record
verified=read(D/'SOURCE_VERIFICATION_RECEIPT.json');members={(x['event'],x['camera']):x for x in verified['members']}
old={}
for role,name in [('front','ACTUAL_RUN_MANIFEST.json'),('back','ACTUAL_BACK_RUN_MANIFEST.json')]:
 for e in read(R/'docs/generated/research_results/mission39'/name)['events']:old[e['event'],role]=e
runid='mission43_vision_'+datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ');base=R/'data/cache'/runid;base.mkdir(mode=0o700,exist_ok=False);(base/'ultralytics_config').mkdir(mode=0o700)
os.environ.update(YOLO_CONFIG_DIR=str(base/'ultralytics_config'),YOLO_AUTOINSTALL='false',YOLO_OFFLINE='true')
cfg=load_frozen_config();manifest=D/'ACTUAL_VISUAL_RUN_MANIFEST.json';run={'schema':'mission43-full-cohort-visual-inference/1','run_id':runid,'started_at_utc':now(),'git_commit':git(),'invocation_sha256':sha(__file__),'canonical_config_sha256':cfg.canonical_hash,'checkpoint_sha256':cfg.checkpoints.vision.expected_sha256,'checkpoint_path':cfg.checkpoints.vision.path,'device':cfg.experiment.device,'seed':cfg.experiment.seed,'source_verification_sha256':sha(D/'SOURCE_VERIFICATION_RECEIPT.json'),'packages':{p:md.version(p)for p in ['torch','ultralytics','av','numpy','opencv-python']},'actual_command':'PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_vision.py','events':[],'private_cache':str(base.relative_to(R)),'reference_status':'Researcher-adopted active AI-assisted annotations; no bbox GT or canonical promotion fabricated','annotation_adoption_sha256':sha(D/'RESEARCHER_ANNOTATION_ADOPTION.json')};save(manifest,run)
with operation('vision'):
 processor=LayerBEventProcessor(R,cache_dir=Path('results/experiments/cache')/runid,config=cfg,vision_only=True)
 for event in INV:
  for role in ['front','back']:
   s=members[event,role];r={'event':event,'camera':role,'source_id':s['source_id'],'source_path':s['path'],'source_sha256':s.get('fresh_sha256'),'annotation':INV[event]['active_proposal_file'],'annotation_sha256':sha(R/INV[event]['active_proposal_file']),'started_at_utc':now()};run['events'].append(r);save(manifest,run);t=time.perf_counter();cpu=time.process_time()
   try:
    assert s['status']=='VERIFIED_EXACT_SOURCE_BYTES_AND_HEADERS','SOURCE_NOT_VERIFIED'
    if(event,role)in old:
     e=old[event,role];payload=R/'docs/generated/research_results/mission39'/e['prediction_file'];assert sha(payload)==e['prediction_sha256'];rows=[json.loads(line)for line in payload.read_text().splitlines()];assert len(rows)==e['sampled_frames']and e['source_sha256_from_AUTH35_V']==s['fresh_sha256']
     r.update(status='REUSED_MISSION39_ACTUAL_INFERENCE',predictions={'path':str(payload.relative_to(R)),'sha256':sha(payload),'records':len(rows)},prior_event_record=e,new_original_inference=False,wall_s_original=e['wall_s'],absolute_video_index=e['absolute_video_index'])
    else:
     original=R/s['path'];assert stat(original)==s['after'],'SOURCE_CHANGED_SINCE_VERIFICATION'
     for op in ['READ_RAW_MEDIA','INFERENCE']:require_media_authorization(original,op,declared_media=True)
     index=s['video']['index'];sid='camera_1'if role=='front'else'camera_2'
     if role=='front':records=processor.process_front_vision(original.parent,video_stream_index=index,run_id=runid,git_commit=run['git_commit'],use_cache=True)
     else:
      prov=processor.build_stream_provenance(cohort=event.split('/')[0],event_id=event.split('/')[1],source_id=sid,modality='vision',run_id=runid,git_commit=run['git_commit'],source_pts=True,video_stream_index=index)
      records=processor.run_vision_inference(original,R/cfg.checkpoints.vision.path,sid,target_fps=cfg.vision.sampling_fps,conf=cfg.vision.confidence_threshold_departure,use_cache=True,provenance=prov,source_pts=True,video_stream_index=index)
     assert records,'EMPTY_STREAM_IS_NOT_A_NEGATIVE_SUCCESS';assert stat(original)==s['after'],'SOURCE_CHANGED_DURING_INFERENCE'
     rows=[(serialize_front_visual_record if role=='front'else serialize_evidence_record)(a)for a in records];artifact=art('predictions/'+event.replace('/','_')+'_'+role+'.jsonl',rows)
     assert all(x['metadata']['timestamp_basis']=='source_pts'and x['metadata']['stream_index']==index for x in rows)
     r.update(status='COMPLETED_ORIGINAL_INFERENCE',predictions=artifact,new_original_inference=True,source_stat_stable=True,absolute_video_index=index,wall_s_original=time.perf_counter()-t,cpu_s=time.process_time()-cpu,finished_at_utc=now(),source_video_timebase=s['video']['time_base'])
     predictor=processor._yolo_model.predictor;run['effective_prediction_options']={k:getattr(predictor.args,k,None)for k in ['imgsz','conf','iou','max_det','rect','half','device','agnostic_nms','classes','augment','seed','mode','task']}
    labels=collections_counter={str(k):{'label':v,'detections':0,'confidence_sum':0.,'confidence_min':None,'confidence_max':None}for k,v in cfg.checkpoints.vision.class_mapping.items()}
    for row in rows:
     for det in row['detections']:
      cid=det.get('class_id',det.get('metadata',{}).get('class_id'));score=det['confidence'];c=labels[str(cid)];c['detections']+=1;c['confidence_sum']+=score;c['confidence_min']=score if c['confidence_min']is None else min(c['confidence_min'],score);c['confidence_max']=score if c['confidence_max']is None else max(c['confidence_max'],score)
    for c in labels.values():c['mean_confidence']=c.pop('confidence_sum')/c['detections']if c['detections']else None
    r.update(sampled_records=len(rows),frames_with_detections=sum(bool(a['detections'])for a in rows),predicted_objects=sum(len(a['detections'])for a in rows),predicted_classes=labels,pts_preserved=True,processing_errors=0,GT_dependent_metrics='UNAVAILABLE_NO_MATCHING_BBOX_REFERENCE_OR_CANONICAL_ACCEPTED_TIMING')
   except Exception as exc:r.update(status='FAILED_ORIGINAL_MEMBER',error_type=type(exc).__name__,error=str(exc),wall_s_attempt=time.perf_counter()-t);traceback.print_exc()
   save(manifest,run);print(json.dumps({k:r[k]for k in ['event','camera','status'] }|{k:r.get(k)for k in ['sampled_records','predicted_objects','wall_s_original','error']}),flush=True)
run.update(finished_at_utc=now(),new_original_members_completed=sum(x['status']=='COMPLETED_ORIGINAL_INFERENCE'for x in run['events']),reused_original_members=sum(x['status']=='REUSED_MISSION39_ACTUAL_INFERENCE'for x in run['events']),failed_members=sum(x['status']=='FAILED_ORIGINAL_MEMBER'for x in run['events']),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);save(manifest,run)
