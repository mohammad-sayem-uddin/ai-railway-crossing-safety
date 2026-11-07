"""One authorized existing five-front B1 acoustic inference and B2 input-assembly run."""
from pathlib import Path
from datetime import datetime,UTC
from fractions import Fraction
import hashlib,json,os,resource,subprocess,sys,time,traceback,importlib.metadata as md
R=Path('/Users/sayemuddin/Desktop/Train_automation');sys.path.insert(0,str(R/'src'))
import av
import numpy as np
import torch
from railway_detection.audio.model import PyTorchTrainHornClassifier
from railway_detection.audio.pipeline import AudioEvidencePipeline
from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.experiments.frozen_config import load_frozen_config,compute_file_sha256
from railway_detection.experiments.layer_b_processor import serialize_evidence_record
from railway_detection.evaluation.cache_only_engine import _validate_visual_record,_validate_audio_record
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.safety.media_guard import require_media_authorization
D=R/'docs/generated/research_results/mission39';A=D/'audio_followup';cfg=load_frozen_config()
verified=json.loads(Path('/private/tmp/mission35_source_verification_6r_s002i/results.json').read_text())['candidates'];members=[c for c in verified if c['camera']=='front' and c['event'] in ['train_events/event_021', 'train_events/event_001', 'no_train_events/event_001']]
front_run=json.loads((D/'ACTUAL_RUN_MANIFEST.json').read_text());front_by={e['event']:e for e in front_run['events']}
for c in members:
 for op in ['READ_RAW_MEDIA','AUDIO_EXTRACTION','FEATURE_EXTRACTION','INFERENCE']:require_media_authorization(R/c['candidate_path'],op,declared_media=True)
run_id='mission39_audio_'+datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ');base=R/'data/cache/b1_audio'/run_id;base.mkdir(parents=True,exist_ok=False);base.chmod(0o700)
for sub in ['predictions','clock_ledgers','assemblies']:(A/sub).mkdir(exist_ok=True)
sha=lambda body:hashlib.sha256(body).hexdigest()
def write_jsonl(relative,rows):
 body=''.join(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n' for row in rows).encode();p=base/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body);p.chmod(0o600);q=A/relative;q.write_bytes(body);return dict(path='audio_followup/'+relative,sha256=sha(body),records=len(rows),bytes=len(body))
def stat_of(p):
 s=p.stat();return {k:getattr(s,k) for k in ['st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns']}
run=dict(schema='mission39-actual-held-out-audio-run/1',run_id=run_id,started_utc=datetime.now(UTC).isoformat(),git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),invocation_source_sha256=sha(Path(__file__).read_bytes()),experiment='B1_audio',stage='ORIGINAL_HELD_OUT_FRONT_AUDIO_INFERENCE',B2_stage='EXISTING_FRONT_AUDIO_COLLECTOR_INPUT_ASSEMBLY_ONLY',accepted_GT_evaluations_executed=0,original_audio_members_planned=3,original_audio_members_completed=0,events=[],config_sha256=cfg.canonical_hash,model_path=cfg.checkpoints.audio_v3.path,model_sha256=cfg.checkpoints.audio_v3.expected_sha256,packages={p:md.version(p) for p in ['torch','av','numpy']},frozen_parameters=dict(sample_rate=16000,window_s=1.0,hop_s=.5,n_fft=512,feature_hop=256,n_mels=64,f_min=80.,f_max=8000.,shape=[64,61],threshold=.37),private_output_base=str(base),actual_command='PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /tmp/m39_run_embedded_audio.py',raw_media_hash_or_probe_repeated=False,raw_audio_files_retained=False,front_vision_inference_repeated=False)
manifest=A/'RETRY_AUDIO_RUN_MANIFEST.json'
def save():manifest.write_text(json.dumps(run,indent=2,allow_nan=False)+'\n')
save()
try:
 # Expected selected checkpoint integrity at point of use; no unrelated vision checkpoint access.
 cp=R/cfg.checkpoints.audio_v3.path;before_model=stat_of(cp);assert compute_file_sha256(cp)==cfg.checkpoints.audio_v3.expected_sha256
 torch.manual_seed(cfg.experiment.seed);np.random.seed(cfg.experiment.seed)
 classifier=PyTorchTrainHornClassifier(checkpoint_path=cp,threshold=cfg.audio.operating_threshold,device=cfg.experiment.device)
 assert stat_of(cp)==before_model;assert classifier.mean==cfg.audio.normalization.mean and classifier.std==cfg.audio.normalization.std and classifier.threshold==.37
 run['model_loaded']=dict(device=str(classifier.device),mean=classifier.mean,std=classifier.std,threshold=classifier.threshold,model_class=type(classifier.model).__name__,torch_threads=torch.get_num_threads(),seed=42,safe_weights_only_load_previously_verified=True,stat_stable=True,model_training=classifier.model.training)
 pipe=AudioEvidencePipeline(classifier=classifier,source_id='audio_1',window_s=cfg.audio.window_s,hop_s=cfg.audio.hop_s,target_sample_rate=cfg.audio.sample_rate,require_classifier=True)
 for c in members:
  event=c['event'];original=R/c['candidate_path'];prefix=event.replace('/','_');began=time.perf_counter();cpu=time.process_time();result=dict(event=event,source_path=c['candidate_path'],container_sha256=c['fresh_sha256'],status='STARTED');run['events'].append(result);save();print(json.dumps(result),flush=True)
  try:
   before=stat_of(original);assert before==c['after'],'Original stat differs from completed AUTH35-V'
   expected=[s for s in c['raw_probe_metadata']['streams'] if s['codec_type']=='audio'];assert len(expected)==1;expected=expected[0]
   require_media_authorization(original,'AUDIO_EXTRACTION',declared_media=True)
   # Audio-only native timing ledger; no image/frame rendering or video decoding.
   ledger=[];previous_end=None;source_samples=0
   with av.open(str(original),mode='r') as container:
    streams=list(container.streams.audio);assert len(streams)==1;stream=streams[0];assert stream.index==expected['index']
    for i,frame in enumerate(container.decode(stream)):
     assert frame.pts is not None and frame.time_base is not None and frame.sample_rate>0
     start=Fraction(frame.pts)*frame.time_base;duration=Fraction(frame.samples,frame.sample_rate)
     assert previous_end is None or start==previous_end,'Noncontiguous decoded audio clock; do not invent fills or offsets'
     ledger.append(dict(index=i,pts=frame.pts,timebase=[frame.time_base.numerator,frame.time_base.denominator],samples=frame.samples,sample_rate=frame.sample_rate,start_fraction=[start.numerator,start.denominator],end_fraction=[(start+duration).numerator,(start+duration).denominator]));previous_end=start+duration;source_samples+=frame.samples
   assert ledger and ledger[0]['start_fraction']==[0,1],'This existing zero-origin route cannot assume nonzero origins'
   ledger_art=write_jsonl('clock_ledgers/'+prefix+'_front_audio_clock.jsonl',ledger)
   require_media_authorization(original,'AUDIO_EXTRACTION',declared_media=True)
   cmd=['ffmpeg','-nostdin','-v','error','-i',str(original),'-map','0:'+str(expected['index']),'-vn','-acodec','pcm_s16le','-ar','16000','-ac','1','-f','s16le','pipe:1']
   start_extract=time.perf_counter();proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False);extract_s=time.perf_counter()-start_extract
   assert proc.returncode==0,proc.stderr.decode(errors='replace');assert len(proc.stdout)>0 and len(proc.stdout)%2==0
   samples=np.frombuffer(proc.stdout,dtype='<i2').astype(np.float64)/32768.;assert np.isfinite(samples).all();sample_count=len(samples)
   # Exact extraction/clock length comparison; no invented source duration or tolerance.
   expected_samples=Fraction(source_samples*16000,ledger[0]['sample_rate']);assert sample_count==(2*expected_samples.numerator+expected_samples.denominator)//(2*expected_samples.denominator),'PCM sample count differs from contiguous native decoded extent'
   assert compute_log_mel_spectrogram(samples[:16000],sample_rate=16000,n_fft=512,hop_length=256,n_mels=64,f_min=80.,f_max=8000.).shape==(64,61)
   for op in ['FEATURE_EXTRACTION','INFERENCE']:require_media_authorization(original,op,declared_media=True)
   records=pipe.process_samples(samples,16000)
   assert records and all(r.available and r.metadata['audio_safety_role']=='supporting_only' for r in records)
   expected_windows=1+(sample_count-16000)//8000;assert len(records)==expected_windows
   rows=[];legacy=[]
   for i,r in enumerate(records):
    m=r.metadata;m.update(source_container_sha256=c['fresh_sha256'],source_audio_stream_index=expected['index'],native_source_timebase=[1,48000],original_audio_start_pts=0,window_start_sample=i*8000,window_end_sample=i*8000+16000,model_sample_rate=16000,causal_end_fraction=[(i*8000+16000)//8000,2],timestamp_basis='native_audio_origin_plus_pcm_sample_offset')
    # Fraction is reduced explicitly; end time is always the causal window end.
    t=Fraction(i*8000+16000,16000);m['causal_end_fraction']=[t.numerator,t.denominator];assert float(t)==r.timestamp_s
    rows.append(serialize_evidence_record(r));prob=m['probability'];assert np.isfinite(prob) and 0<=prob<=1
    row=dict(window_index=i,start_sec=i*.5,end_sec=i*.5+1,horn_confidence=prob,is_horn_detected=prob>=.37);_validate_audio_record(row,i);legacy.append(row)
   predictions=write_jsonl('predictions/'+prefix+'_front_audio.jsonl',rows);cache=write_jsonl('predictions/'+prefix+'_front_audio_descriptive_rows.jsonl',legacy)
   # Reuse byte-bound original front predictions; no model initialization/vision reread.
   f=front_by[event];data=(D/f['prediction_file']).read_bytes();assert sha(data)==f['prediction_sha256'];vision=[_validate_visual_record(json.loads(line),i) for i,line in enumerate(data.decode().splitlines())]
   collector=MultimodalEvidenceCollector(window_tolerance_s=.25);collector.add_evidence_batch(vision);collector.add_evidence_batch(records);assert not collector.rejected_observations
   endpoint=max(vision[-1].timestamp_s,records[-1].timestamp_s)
   frames=collector.generate_frames_from_history(0.,endpoint,stride_s=cfg.timing.tick_s);assembly=[]
   for frame in frames:
    assert all(r.timestamp_s<=frame.master_timestamp_s+1e-6 for r in (*frame.vision_records,*frame.audio_records))
    assembly.append(dict(master_timestamp_s=frame.master_timestamp_s,front_prediction_timestamps=[r.timestamp_s for r in frame.vision_records],causal_audio_window_end_timestamps=[r.timestamp_s for r in frame.audio_records],front_predicted_objects=sum(len(r.detections) for r in frame.vision_records),audio_probabilities=[r.metadata['probability'] for r in frame.audio_records],audio_predicted_train=[r.metadata['probability']>=.37 for r in frame.audio_records],stage='B2_INPUT_ASSEMBLY_ONLY_NO_DECISION_REPLAY'))
   assembly_art=write_jsonl('assemblies/'+prefix+'_B2_front_inputs.jsonl',assembly)
   after=stat_of(original);assert after==before,'Source changed during acoustic processing'
   probs=[r.metadata['probability'] for r in records];positives=sum(p>=.37 for p in probs)
   result.update(status='COMPLETED_ORIGINAL_AUDIO_INFERENCE',source_stat_stable=True,absolute_audio_stream_index=expected['index'],native_audio_clock_contiguous=True,native_audio_first_pts=ledger[0]['pts'],native_audio_timebase=ledger[0]['timebase'],decoded_audio_frames=len(ledger),native_decoded_sample_count=source_samples,native_sample_rate=ledger[0]['sample_rate'],pcm16k_mono_samples=sample_count,pcm_audio_sha256=sha(proc.stdout),pcm_retained=False,decoded_sample_duration_s=float(previous_end),window_count=len(records),predicted_train_windows=positives,predicted_ambient_windows=len(records)-positives,probability_min=min(probs),probability_max=max(probs),probability_mean=sum(probs)/len(probs),unwindowed_tail_samples=sample_count-(int((len(records)-1)*8000)+16000),clock_ledger=ledger_art,predictions=predictions,descriptive_cache_rows=cache,ffmpeg_command=cmd,ffmpeg_returncode=proc.returncode,ffmpeg_stderr=proc.stderr.decode(errors='replace'),ffmpeg_extraction_wall_s=extract_s,B2_input_assembly=assembly_art,B2_frames_with_both_stream_records=sum(bool(f.vision_records) and bool(f.audio_records) for f in frames),B2_frames_with_vision_records=sum(bool(f.vision_records) for f in frames),B2_frames_with_audio_records=sum(bool(f.audio_records) for f in frames),B2_front_prediction_parent_sha256=f['prediction_sha256'],B2_decision_replay_executed=False,wall_s=time.perf_counter()-began,cpu_s=time.process_time()-cpu)
   run['original_audio_members_completed']+=1
   del samples,proc,records,vision,collector,frames
  except Exception as exc:
   result.update(status='FAILED_ORIGINAL_AUDIO_MEMBER',error_type=type(exc).__name__,error=str(exc),wall_s=time.perf_counter()-began);traceback.print_exc()
  finally:save();print(json.dumps(result),flush=True)
finally:
 run.update(finished_utc=datetime.now(UTC).isoformat(),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);save()
if run['original_audio_members_completed']!=3:sys.exit(1)
