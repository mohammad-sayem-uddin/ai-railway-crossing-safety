"""Original-source frame and signal diagnostics, with no model inference or new GT."""
from common import *
from fractions import Fraction
import av,numpy as np,tempfile,time,traceback
from PIL import Image,ImageDraw
from railway_detection.safety.media_guard import require_media_authorization,require_media_command_authorization
from railway_detection.audio.features import compute_log_mel_spectrogram
plan=read(D/'SOURCE_DIAGNOSTIC_PLAN.json');private=Path(tempfile.mkdtemp(prefix='mission44_actual_source_diagnostics_',dir='/private/tmp'));private.chmod(0o700)
receipt={'schema':'mission44-actual-source-diagnostics/1','started_at_utc':now(),'invocation_sha256':sha(__file__),'selection_sha256':sha(D/'SOURCE_DIAGNOSTIC_PLAN.json'),'evidence_classification':'ACTUAL_ORIGINAL_SOURCE_NOT_SYNTHETIC','private_frame_directory':str(private),'private_frame_pixels_not_packaged':True,'inference_runs':0,'model_checkpoint_access':False,'original_container_hash_or_probe_repeated':False,'visual_cases':[],'audio_cases':[]};save(D/'SOURCE_DIAGNOSTIC_RECEIPT.json',receipt)
frame_rows=[];signal_rows=[];spectrum_rows=[]
with source_operation():
 for case in plan['visual_cases']:
  s=case['source'];p=R/s['path'];r={'event':case['event'],'camera':case['camera'],'case_type':case['case_type'],'source_path':s['path'],'source_sha256_from_M43':s['fresh_sha256'],'selected_frames':[]};receipt['visual_cases'].append(r);began=time.perf_counter()
  try:
   before=stat(p);assert before==s['after'],'SOURCE_CHANGED_SINCE_M43'
   targets={x['frame_index']:x for x in case['targets']};images=[]
   require_media_authorization(p,'READ_RAW_MEDIA',declared_media=True);require_media_authorization(p,'FRAME_EXTRACTION',declared_media=True)
   with av.open(str(p),mode='r')as container:
    stream=next(x for x in container.streams.video if x.index==s['video']['index'])
    for i,frame in enumerate(container.decode(stream)):
     if i not in targets:continue
     target=targets[i];assert frame.pts==target['source_pts_ticks']and [frame.time_base.numerator,frame.time_base.denominator]==target['timebase'],'FRAME_CLOCK_DIFFERS_FROM_ACTUAL_INFERENCE'
     image=Image.fromarray(frame.to_ndarray(format='rgb24'));original_size=list(image.size);draw=ImageDraw.Draw(image)
     for det in target['existing_model_detections']:
      box=det.get('bbox_xyxy',det.get('bbox'));label=det.get('class_name',det.get('label',str(det.get('class_id'))));draw.rectangle(box,outline=(255,80,20),width=max(2,image.width//400));draw.text((box[0],max(0,box[1]-16)),f'{label} {det["confidence"]:.3f}',fill=(255,80,20))
     image.thumbnail((760,440));tile=Image.new('RGB',(780,480),'white');tile.paste(image,((780-image.width)//2,30));ImageDraw.Draw(tile).text((8,6),f'Actual frame {i}; PTS={frame.pts}*{frame.time_base}; t={target["source_timestamp_s"]:.6f}s',fill='black');images.append(tile)
     r['selected_frames'].append({'frame_index':i,'pts_ticks':frame.pts,'timebase':target['timebase'],'timestamp_s':target['source_timestamp_s'],'image_dimensions':original_size,'inference_prediction_row':target['prediction_row_index'],'model_objects':len(target['existing_model_detections'])});frame_rows.append({'event':case['event'],'camera':case['camera'],'case_type':case['case_type'],'frame_index':i,'pts_ticks':frame.pts,'timebase':str(frame.time_base),'source_time_s':target['source_timestamp_s'],'width':original_size[0],'height':original_size[1],'existing_model_objects':len(target['existing_model_detections']),'source_sha256_from_M43':s['fresh_sha256'],'source_link':s['path'],'frame_clock_matches_inference':True,'new_annotation_or_GT':False})
     if len(images)==len(targets):break
   assert len(images)==len(targets)and stat(p)==before
   sheet=Image.new('RGB',(1560,80+480*((len(images)+1)//2)),(235,235,235));ImageDraw.Draw(sheet).text((15,15),case['event']+' / '+case['camera']+' / '+case['case_type']+' -- ACTUAL SOURCE DIAGNOSTIC; NO GT',fill='black')
   for i,image in enumerate(images):sheet.paste(image,((i%2)*780,60+(i//2)*480))
   outfile=private/(case['event'].replace('/','_')+'_'+case['camera']+'_actual.png');sheet.save(outfile);outfile.chmod(0o600);r.update(status='ACTUAL_SELECTED_FRAMES_DECODED',private_contact_sheet=str(outfile),private_contact_sheet_sha256=sha(outfile),source_stat_stable=True,wall_s=time.perf_counter()-began)
  except Exception as exc:r.update(status='FAILED_DIAGNOSTIC',error_type=type(exc).__name__,error=str(exc));traceback.print_exc()
  save(D/'SOURCE_DIAGNOSTIC_RECEIPT.json',receipt);print(json.dumps({k:r[k]for k in ['event','camera','status']}),flush=True)
 for case in plan['audio_errors']:
  e=case['audio_record'];s=case['source'];p=R/s['path'];bound=e.get('prior_event_record',e);r={'event':case['event'],'error_type':case['error_type'],'source_path':s['path'],'source_sha256_from_M43':s['fresh_sha256'],'adopted_annotation':case['annotation'],'windows':[]};receipt['audio_cases'].append(r);began=time.perf_counter()
  try:
   before=stat(p);assert before==s['after'];index=e['absolute_audio_stream_index'];cmd=['ffmpeg','-nostdin','-v','error','-i',str(p),'-map','0:'+str(index),'-vn','-acodec','pcm_s16le','-ar','16000','-ac','1','-f','s16le','pipe:1'];require_media_command_authorization(cmd,'AUDIO_EXTRACTION');proc=subprocess.run(cmd,capture_output=True,check=False);assert proc.returncode==0,proc.stderr.decode(errors='replace');pcmsha=hashlib.sha256(proc.stdout).hexdigest();assert pcmsha==bound['pcm_audio_sha256'],'ACTUAL_PCM_DIFFERS_FROM_INFERENCE_INPUT';samples=np.frombuffer(proc.stdout,dtype='<i2').astype(np.float64)/32768.;pred=payload(e['predictions']);score=[x['metadata']['probability']for x in pred];selected=set(sorted(range(len(pred)),key=lambda i:(-score[i],i))[:3]);ann=read(R/case['annotation']);onset=ann.get('proposed_train_metadata',{}).get('horn_onset_s')
   if isinstance(onset,(int,float)):selected.update(i for i,x in enumerate(pred)if x['metadata']['window_start_s']<=onset<x['timestamp_s'])
   require_media_authorization(p,'FEATURE_EXTRACTION',declared_media=True)
   for i in sorted(selected):
    w=samples[i*8000:i*8000+16000];assert len(w)==16000;frames=np.lib.stride_tricks.sliding_window_view(w,512)[::256];power=(np.abs(np.fft.rfft(frames*np.hanning(512),axis=1))**2).mean(axis=0);freq=np.fft.rfftfreq(512,1/16000);power_sum=power.sum();centroid=float((freq*power).sum()/power_sum)if power_sum else None;flatness=float(np.exp(np.mean(np.log(power+1e-12)))/(power.mean()+1e-12));logmel=compute_log_mel_spectrogram(w,sample_rate=16000,n_fft=512,hop_length=256,n_mels=64,f_min=80.,f_max=8000.,log_scale='natural');assert logmel.shape==(64,61)
    row={'event':case['event'],'error_type':case['error_type'],'window_index':i,'window_start_s':i*.5,'causal_window_end_s':pred[i]['timestamp_s'],'model_score_from_M43':score[i],'selection':'TOP_EXISTING_SCORE'if i in sorted(range(len(pred)),key=lambda i:(-score[i],i))[:3]else'CONTAINS_ADOPTED_ONSET_IF_FRONT_CLOCK','rms_normalized_pcm':float(np.sqrt(np.mean(w*w))),'absolute_peak_normalized_pcm':float(np.max(np.abs(w))),'clipped_sample_fraction':float(np.mean(np.abs(w)>=32767/32768)),'zero_crossing_fraction':float(np.mean(np.signbit(w[1:])!=np.signbit(w[:-1]))),'dominant_non_DC_frequency_hz':float(freq[1+np.argmax(power[1:])]),'spectral_centroid_hz':centroid,'spectral_flatness':flatness,'natural_log_mel_mean':float(logmel.mean()),'natural_log_mel_std':float(logmel.std()),'PCM_input_identity_matches_M43':True,'signal_category_or_window_truth':'NOT_ESTABLISHED; numerical descriptors are not a horn label'};signal_rows.append(row);r['windows'].append(row)
    for f,power_value in zip(freq,power):spectrum_rows.append({'event':case['event'],'window_index':i,'frequency_hz':float(f),'mean_STFT_power':float(power_value),'FFT':512,'hop':256,'signal_source':'Actual prior-model-input PCM; no model inference or new truth'})
   r.update(status='ACTUAL_PCM_IDENTITY_AND_SIGNAL_DIAGNOSTICS_COMPLETE',audio_stream_index=index,pcm_sha256=pcmsha,PCM_matches_prior_model_input=True,PCM_retained=False,sample_count=len(samples),duration_s=len(samples)/16000,ffmpeg_command=cmd,ffmpeg_stderr=proc.stderr.decode(errors='replace'),source_stat_stable=stat(p)==before,wall_s=time.perf_counter()-began);assert r['source_stat_stable'];del samples,proc
  except Exception as exc:r.update(status='FAILED_DIAGNOSTIC',error_type=type(exc).__name__,error=str(exc));traceback.print_exc()
  save(D/'SOURCE_DIAGNOSTIC_RECEIPT.json',receipt);print(json.dumps({k:r[k]for k in ['event','status']}),flush=True)
receipt.update(finished_at_utc=now(),decoded_selected_frames=len(frame_rows),visual_cases_completed=sum(x['status']=='ACTUAL_SELECTED_FRAMES_DECODED'for x in receipt['visual_cases']),audio_cases_completed=sum(x['status']=='ACTUAL_PCM_IDENTITY_AND_SIGNAL_DIAGNOSTICS_COMPLETE'for x in receipt['audio_cases']),operator_human_listening_performed=False,sound_category_not_inferred_from_spectrum=True);save(D/'SOURCE_DIAGNOSTIC_RECEIPT.json',receipt);table('SOURCE_FRAME_DIAGNOSTICS.csv',frame_rows);table('AUDIO_SIGNAL_WINDOW_DIAGNOSTICS.csv',signal_rows);table('AUDIO_SIGNAL_SPECTRUM.csv',spectrum_rows)
