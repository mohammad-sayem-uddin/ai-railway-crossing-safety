"""Actual five-front inference stage; never invoked without canonical point-of-use scope."""
from pathlib import Path
from datetime import datetime,UTC
import sys,json,time,hashlib,os,resource,traceback,subprocess,importlib.metadata as md
R=Path('/Users/sayemuddin/Desktop/Train_automation');sys.path.insert(0,str(R/'src'))
from railway_detection.safety.media_guard import require_media_authorization
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor,serialize_front_visual_record
D=R/'docs/generated/research_results/mission39'
verified=json.loads(Path('/private/tmp/mission35_source_verification_6r_s002i/results.json').read_text())['candidates']
subjects={v['event']:v for v in verified if v['camera']=='front'}
events=[('train_events/event_005',0),('train_events/event_021',0),('engine_events/event_001',0),('train_events/event_001',0),('no_train_events/event_001',1)]
# The real guard reads the actual canonical grant; no temporary root/override/patch.
for event,index in events:
 path=R/'data/raw/layer_b/v2'/event/'camera_front.mov'
 require_media_authorization(path,'READ_RAW_MEDIA',declared_media=True)
 require_media_authorization(path,'INFERENCE',declared_media=True)
run_id='mission39_'+datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
base=R/'data/cache/b0_front'/run_id;base.mkdir(parents=True,exist_ok=False);base.chmod(0o700)
configdir=base/'ultralytics_config';configdir.mkdir(mode=0o700)
os.environ.update(YOLO_CONFIG_DIR=str(configdir),YOLO_AUTOINSTALL='false',YOLO_OFFLINE='true')
config=load_frozen_config();git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
# Existing selected-checkpoint integrity at the actual runtime boundary is not bypassed.
# No stand-alone repeat verification, other checkpoint or original-media hash/probe.
processor=LayerBEventProcessor(R,cache_dir=Path('results/experiments/cache')/run_id,config=config,vision_only=True)
records_dir=D/'predictions';records_dir.mkdir(exist_ok=True)
summary=[];manifest=dict(manifest_version='1.0.0',created_at=datetime.now(UTC).isoformat(),cohort='fixed_five_front',events={})
run=dict(experiment_id='M36-B0_FRONT-FIVE',stage='ORIGINAL_SOURCE_INFERENCE_AND_DESCRIPTIVE_PREDICTIONS',reference_dependent_evaluation_executed=False,run_id=run_id,git_commit=git_commit,invocation_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),checkpoint_sha256=config.checkpoints.vision.expected_sha256,canonical_config_sha256=config.canonical_hash,packages={p:md.version(p) for p in ['torch','ultralytics','av','numpy','opencv-python']},device='cpu',seed=42,output_base=str(base),started_utc=datetime.now(UTC).isoformat(),events=summary,canonical_gt='NOT_ESTABLISHED',reported_human_review_complete=True)
(D/'ACTUAL_RUN_MANIFEST.json').write_text(json.dumps(run,indent=2)+'\n')
try:
 for event,index in events:
  print(json.dumps(dict(event=event,status='STARTING',absolute_video_index=index)),flush=True)
  started=time.perf_counter();cpu=time.process_time()
  try:
   original=R/'data/raw/layer_b/v2'/event/'camera_front.mov'
   current=original.stat();bound=subjects[event]['after']
   for key in ['st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns']:
    if getattr(current,key)!=bound[key]:raise ValueError('Source identity changed since AUTH35-V: '+key)
   records=processor.process_front_vision(R/'data/raw/layer_b/v2'/event,video_stream_index=index,run_id=run_id,git_commit=git_commit,use_cache=True)
   after=original.stat()
   if any(getattr(current,k)!=getattr(after,k) for k in ['st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns']):raise ValueError('Source changed during inference')
   rows=[serialize_front_visual_record(r) for r in records]
   if not rows:raise ValueError('No actual prediction records; not a negative success')
   name=event.replace('/','_')+'_front.jsonl';payload=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows)
   actual=base/name;actual.write_text(payload);actual.chmod(0o600)
   (records_dir/name).write_text(payload)
   classes={str(k):dict(label=v,detections=0,scores=[]) for k,v in config.checkpoints.vision.class_mapping.items()}
   for row in rows:
    for det in row['detections']:
     c=classes[str(det['class_id'])];c['detections']+=1;c['scores'].append(det['confidence'])
   for c in classes.values():
    s=c.pop('scores');c['mean_confidence']=sum(s)/len(s) if s else None
   result=dict(event=event,source_id=subjects[event]['source_id'],source_sha256_from_AUTH35_V=subjects[event]['fresh_sha256'],source_stat_stable=True,status='COMPLETED_ORIGINAL_INFERENCE',camera='front',absolute_video_index=index,sampled_frames=len(rows),frames_with_detections=sum(bool(r['detections']) for r in rows),first_sample_s=rows[0]['timestamp_sec'],last_sample_s=rows[-1]['timestamp_sec'],wall_s=time.perf_counter()-started,cpu_s=time.process_time()-cpu,predicted_classes=classes,prediction_sha256=hashlib.sha256(payload.encode()).hexdigest(),prediction_file='predictions/'+name,pts_preserved=all(r['metadata']['timestamp_basis']=='source_pts' for r in rows),GT_dependent_metrics='UNAVAILABLE_NO_ACCEPTED_CANONICAL_FIELDS')
   predictor=processor._yolo_model.predictor
   run['effective_prediction_options']={k:getattr(predictor.args,k,None) for k in ['imgsz','conf','iou','max_det','rect','half','device','agnostic_nms','classes','augment','seed','mode','task']}
   summary.append(result)
   manifest['events'][event]=dict(event_id=event,front_vision_cache=dict(path=str(actual.relative_to(R)),sha256=result['prediction_sha256'],byte_size=len(payload.encode()),line_count=len(rows)))
   print(json.dumps(result),flush=True)
  except Exception as exc:
   summary.append(dict(event=event,status='FAILED_ORIGINAL_INFERENCE',error_type=type(exc).__name__,error=str(exc),wall_s=time.perf_counter()-started));traceback.print_exc();raise
finally:
 run.update(finished_utc=datetime.now(UTC).isoformat(),original_events_completed=sum(e['status']=='COMPLETED_ORIGINAL_INFERENCE' for e in summary),planned_events=5,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 (D/'ACTUAL_RUN_MANIFEST.json').write_text(json.dumps(run,indent=2)+'\n')
 if manifest['events']:(base/'cache_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
