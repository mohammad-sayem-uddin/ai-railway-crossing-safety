"""Existing corrected B1_front embedded-audio method on22 new events; reuse five actual runs."""
from common import *
from fractions import Fraction
import av,numpy as np,torch,time,traceback,resource,importlib.metadata as md
from railway_detection.safety.media_guard import require_media_authorization,require_media_command_authorization
from railway_detection.audio.model import PyTorchTrainHornClassifier
from railway_detection.audio.pipeline import AudioEvidencePipeline
from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.experiments.frozen_config import load_frozen_config,compute_file_sha256
from railway_detection.experiments.layer_b_processor import serialize_evidence_record
from railway_detection.evaluation.cache_only_engine import _validate_visual_record,_validate_audio_record
from railway_detection.fusion.collector import MultimodalEvidenceCollector
cfg=load_frozen_config();members={(x['event'],x['camera']):x for x in read(D/'SOURCE_VERIFICATION_RECEIPT.json')['members']}
prior=read(R/'docs/generated/research_results/mission39/audio_followup/CORRECTED_AUDIO_RUN_MANIFEST.json');old={e['event']:e for e in prior['events']}
front={e['event']:e for e in read(D/'ACTUAL_VISUAL_RUN_MANIFEST.json')['events']if e['camera']=='front'and e['status']in ['COMPLETED_ORIGINAL_INFERENCE','REUSED_MISSION39_ACTUAL_INFERENCE']}
runid='mission43_audio_'+datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ');run={'schema':'mission43-full-cohort-audio-input-run/1','run_id':runid,'started_at_utc':now(),'git_commit':git(),'invocation_sha256':sha(__file__),'actual_command':'PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_audio.py','model_path':cfg.checkpoints.audio_v3.path,'model_sha256':cfg.checkpoints.audio_v3.expected_sha256,'canonical_config_sha256':cfg.canonical_hash,'annotation_adoption_sha256':sha(D/'RESEARCHER_ANNOTATION_ADOPTION.json'),'packages':{p:md.version(p)for p in ['torch','av','numpy']},'frozen_parameters':dict(sample_rate=16000,window_s=1.0,hop_s=.5,n_fft=512,feature_hop=256,n_mels=64,f_min=80.,f_max=8000.,shape=[64,61],threshold=.37,log_scale='natural',log_epsilon=1e-10,normalization_mean=cfg.audio.normalization.mean,normalization_std=cfg.audio.normalization.std,device=cfg.experiment.device,seed=cfg.experiment.seed),'events':[],'original_PCM_retained':False,'B2_decision_replay_executed':False};manifest=D/'ACTUAL_AUDIO_RUN_MANIFEST.json';save(manifest,run)
with operation('audio'):
 cp=R/cfg.checkpoints.audio_v3.path;modelstat=stat(cp);assert compute_file_sha256(cp)==cfg.checkpoints.audio_v3.expected_sha256
 torch.manual_seed(cfg.experiment.seed);np.random.seed(cfg.experiment.seed);classifier=PyTorchTrainHornClassifier(checkpoint_path=cp,threshold=cfg.audio.operating_threshold,device=cfg.experiment.device);assert stat(cp)==modelstat
 assert classifier.mean==cfg.audio.normalization.mean and classifier.std==cfg.audio.normalization.std and classifier.threshold==.37
 pipe=AudioEvidencePipeline(classifier=classifier,source_id='audio_1',window_s=cfg.audio.window_s,hop_s=cfg.audio.hop_s,target_sample_rate=cfg.audio.sample_rate,require_classifier=True)
 for event in INV:
  s=members[event,'front'];r={'event':event,'source_id':s['source_id'],'source_path':s['path'],'container_sha256':s.get('fresh_sha256'),'annotation_file':INV[event]['active_proposal_file'],'annotation_sha256':sha(R/INV[event]['active_proposal_file']),'started_at_utc':now()};run['events'].append(r);save(manifest,run);began=time.perf_counter();cpu=time.process_time()
  try:
   assert s['status']=='VERIFIED_EXACT_SOURCE_BYTES_AND_HEADERS','SOURCE_NOT_VERIFIED'
   if event in old:
    e=old[event];assert e['container_sha256']==s['fresh_sha256'];arts={}
    for key in ['clock_ledger','predictions','descriptive_cache_rows','B2_input_assembly']:
     value=e[key].copy();p=R/'docs/generated/research_results/mission39'/value['path'];assert sha(p)==value['sha256'];value['path']=str(p.relative_to(R));arts[key]=value
    r.update(status='REUSED_MISSION39_CORRECTED_AUDIO',new_original_inference=False,prior_event_record=e,**arts,window_count=e['window_count'],predicted_train_windows=e['predicted_train_windows'],probability_mean=e['probability_mean'],unwindowed_tail_samples=e['unwindowed_tail_samples'],absolute_audio_stream_index=e['absolute_audio_stream_index'],wall_s_original=e['wall_s'],B2_frames_with_both_stream_records=e['B2_frames_with_both_stream_records'],B2_front_prediction_parent_sha256=e['B2_front_prediction_parent_sha256'])
   else:
    original=R/s['path'];assert stat(original)==s['after'],'SOURCE_CHANGED_SINCE_VERIFICATION';assert len(s['audio'])==1,'MISSING_OR_AMBIGUOUS_AUDIO_STREAM';index=s['audio'][0]['index'];before=stat(original)
    require_media_authorization(original,'AUDIO_EXTRACTION',declared_media=True);ledger=[];previous=None;total=0
    with av.open(str(original),mode='r')as container:
     streams=list(container.streams.audio);assert len(streams)==1;stream=streams[0];assert stream.index==index
     for i,frame in enumerate(container.decode(stream)):
      assert frame.pts is not None and frame.time_base is not None and frame.sample_rate>0
      start=Fraction(frame.pts)*frame.time_base;duration=Fraction(frame.samples,frame.sample_rate);assert previous is None or start==previous,'NONCONTIGUOUS_NATIVE_AUDIO_NO_FILL_PERMITTED';previous=start+duration;total+=frame.samples
      ledger.append(dict(index=i,pts=frame.pts,timebase=[frame.time_base.numerator,frame.time_base.denominator],samples=frame.samples,sample_rate=frame.sample_rate,start_fraction=[start.numerator,start.denominator],end_fraction=[previous.numerator,previous.denominator]))
    assert ledger and ledger[0]['start_fraction']==[0,1],'EXISTING_ZERO_ORIGIN_ROUTE_NOT_APPLICABLE'
    cmd=['ffmpeg','-nostdin','-v','error','-i',str(original),'-map','0:'+str(index),'-vn','-acodec','pcm_s16le','-ar','16000','-ac','1','-f','s16le','pipe:1'];require_media_command_authorization(cmd,'AUDIO_EXTRACTION');proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False);assert proc.returncode==0,proc.stderr.decode(errors='replace');assert proc.stdout and len(proc.stdout)%2==0
    samples=np.frombuffer(proc.stdout,dtype='<i2').astype(np.float64)/32768.;assert np.isfinite(samples).all();n=len(samples);expected=Fraction(total*16000,ledger[0]['sample_rate']);assert n==(2*expected.numerator+expected.denominator)//(2*expected.denominator),'PCM_RESAMPLING_EXTENT_MISMATCH';assert n>=16000,'NO_COMPLETE_EXISTING_WINDOW'
    for op in ['FEATURE_EXTRACTION','INFERENCE']:require_media_authorization(original,op,declared_media=True)
    assert compute_log_mel_spectrogram(samples[:16000],sample_rate=16000,n_fft=512,hop_length=256,n_mels=64,f_min=80.,f_max=8000.,log_scale='natural').shape==(64,61)
    records=pipe.process_samples(samples,16000);assert len(records)==1+(n-16000)//8000;rows=[];legacy=[]
    for i,rec in enumerate(records):
     t=Fraction(i*8000+16000,16000);assert rec.timestamp_s==float(t)and rec.available;rec.metadata.update(source_container_sha256=s['fresh_sha256'],source_audio_stream_index=index,native_source_timebase=ledger[0]['timebase'],original_audio_start_pts=ledger[0]['pts'],window_start_sample=i*8000,window_end_sample=i*8000+16000,model_sample_rate=16000,causal_end_fraction=[t.numerator,t.denominator],timestamp_basis='native_audio_origin_plus_pcm_sample_offset',feature_log_scale='natural',feature_log_epsilon=1e-10)
     rows.append(serialize_evidence_record(rec));prob=rec.metadata['probability'];assert np.isfinite(prob)and 0<=prob<=1;lr=dict(window_index=i,start_sec=i*.5,end_sec=i*.5+1,horn_confidence=prob,is_horn_detected=prob>=.37);_validate_audio_record(lr,i);legacy.append(lr)
    prefix=event.replace('/','_');r.update(predictions=art('audio_predictions/'+prefix+'_front_audio.jsonl',rows),descriptive_cache_rows=art('audio_predictions/'+prefix+'_front_audio_descriptive_rows.jsonl',legacy),clock_ledger=art('audio_clocks/'+prefix+'_front_audio_clock.jsonl',ledger),status='COMPLETED_ORIGINAL_AUDIO_INFERENCE',new_original_inference=True,window_count=len(rows),predicted_train_windows=sum(a['metadata']['probability']>=.37 for a in rows),probability_mean=float(np.mean([a['metadata']['probability']for a in rows])),unwindowed_tail_samples=n-((len(rows)-1)*8000+16000),absolute_audio_stream_index=index,pcm_audio_sha256=hashlib.sha256(proc.stdout).hexdigest(),native_audio_timebase=ledger[0]['timebase'],native_audio_first_pts=ledger[0]['pts'],native_decoded_sample_count=total,native_sample_rate=ledger[0]['sample_rate'],pcm16k_mono_samples=n,native_audio_clock_contiguous=True,PCM_retained=False,ffmpeg_command=cmd,ffmpeg_returncode=proc.returncode,ffmpeg_stderr=proc.stderr.decode(errors='replace'))
    if event in front:
     f=front[event];payload=R/f['predictions']['path'];assert sha(payload)==f['predictions']['sha256'];visual=[_validate_visual_record(json.loads(line),i)for i,line in enumerate(payload.read_text().splitlines())];collector=MultimodalEvidenceCollector(window_tolerance_s=.25);collector.add_evidence_batch(visual);collector.add_evidence_batch(records);assert not collector.rejected_observations;frames=collector.generate_frames_from_history(0.,max(visual[-1].timestamp_s,records[-1].timestamp_s),stride_s=cfg.timing.tick_s);assembled=[]
     for frame in frames:
      assert all(a.timestamp_s<=frame.master_timestamp_s+1e-6 for a in (*frame.vision_records,*frame.audio_records))
      assembled.append(dict(master_timestamp_s=frame.master_timestamp_s,front_prediction_timestamps=[a.timestamp_s for a in frame.vision_records],causal_audio_window_end_timestamps=[a.timestamp_s for a in frame.audio_records],front_predicted_objects=sum(len(a.detections)for a in frame.vision_records),audio_probabilities=[a.metadata['probability']for a in frame.audio_records],audio_predicted_train=[a.metadata['probability']>=.37 for a in frame.audio_records],stage='B2_INPUT_ASSEMBLY_ONLY_NO_DECISION_REPLAY'))
     r.update(B2_input_assembly=art('assemblies/'+prefix+'_B2_front_inputs.jsonl',assembled),B2_frames_with_both_stream_records=sum(bool(a.vision_records)and bool(a.audio_records)for a in frames),B2_front_prediction_parent_sha256=f['predictions']['sha256'])
    else:r['B2_input_status']='BLOCKED_MISSING_FRONT_PREDICTIONS; independent audio inference retained'
    assert stat(original)==before,'SOURCE_CHANGED_DURING_AUDIO';r.update(source_stat_stable=True,wall_s_original=time.perf_counter()-began,cpu_s=time.process_time()-cpu,finished_at_utc=now());del samples,proc,records
   r['GT_dependent_metrics']='MISSING_EXACT_WINDOW_LABELS_OR_ACCEPTED_CANONICAL_BOUNDARIES; adopted candidate content retained'
  except Exception as exc:r.update(status='FAILED_ORIGINAL_AUDIO_MEMBER',error_type=type(exc).__name__,error=str(exc),wall_s_attempt=time.perf_counter()-began);traceback.print_exc()
  save(manifest,run);print(json.dumps({k:r[k]for k in ['event','status']}|{k:r.get(k)for k in ['window_count','predicted_train_windows','wall_s_original','error']}),flush=True)
run.update(finished_at_utc=now(),new_original_members_completed=sum(x['status']=='COMPLETED_ORIGINAL_AUDIO_INFERENCE'for x in run['events']),reused_members=sum(x['status']=='REUSED_MISSION39_CORRECTED_AUDIO'for x in run['events']),failed_members=sum(x['status']=='FAILED_ORIGINAL_AUDIO_MEMBER'for x in run['events']),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);save(manifest,run)
