"""Display-matrix regression tests use generated pixels/codecs, never original recordings."""
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
import subprocess
import numpy as np
import pytest
from railway_detection.vision import video
from railway_detection.config.exceptions import ConfigError
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor,serialize_evidence_record,deserialize_evidence_record
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.experiments.cache_provenance import CacheProvenanceError
av=pytest.importorskip('av',minversion='18.1')

def generated_rotated(tmp_path,rotation):
 base=tmp_path/'generated_base.mp4';out=tmp_path/'generated_rotated.mp4';pixels=np.zeros((48,80,3),np.uint8);pixels[:24,:40]=[230,20,10];pixels[:24,40:]=[15,210,20];pixels[24:,:40]=[20,30,220];pixels[24:,40:]=[230,210,20]
 with av.open(str(base),'w')as c:
  stream=c.add_stream('libx264',rate=5);stream.width=80;stream.height=48;stream.pix_fmt='yuv420p'
  for i in range(4):
   f=av.VideoFrame.from_ndarray(pixels,format='bgr24');f.pts=i;f.time_base=Fraction(1,5)
   for packet in stream.encode(f):c.mux(packet)
  for packet in stream.encode():c.mux(packet)
 subprocess.run(['ffmpeg','-nostdin','-v','error','-display_rotation:v:0',str(rotation),'-i',str(base),'-c','copy',str(out)],check=True,capture_output=True)
 return out

@pytest.mark.parametrize('rotation',[-90,90,180,0])
def test_real_generated_display_matrix_preserves_pts_and_spatial_pixels(tmp_path,rotation):
 path=generated_rotated(tmp_path,rotation)
 with av.open(str(path))as c:raw=list(c.decode(video=0))
 frames=list(video.frame_generator(path,source_pts=True,target_fps=5))
 assert len(frames)==len(raw)==4
 for observed,decoded in zip(frames,raw):
  expected=np.ascontiguousarray(np.rot90(decoded.to_ndarray(format='bgr24'),k=decoded.rotation//90))
  np.testing.assert_array_equal(observed.image,expected)
  assert observed.image.flags.c_contiguous
  assert observed.pts_ticks==decoded.pts and observed.timebase==(decoded.time_base.numerator,decoded.time_base.denominator)
  assert observed.timestamp_s==float(decoded.pts*decoded.time_base)
  assert observed.display_rotation_deg==decoded.rotation

@pytest.mark.parametrize('rotation',[45,True,None])
def test_unsupported_or_malformed_display_rotation_fails_closed(tmp_path,monkeypatch,rotation):
 path=tmp_path/'constructed.mkv';path.touch();f=SimpleNamespace(pts=900,time_base=Fraction(1,600),rotation=rotation,to_ndarray=lambda **kw:np.zeros((4,6,3),np.uint8));stream=SimpleNamespace(index=0,start_time=900)
 class Container:
  streams=SimpleNamespace(video=[stream])
  def __enter__(self):return self
  def __exit__(self,*args):return False
  def decode(self,selected):return iter([f])
 monkeypatch.setattr(av,'open',lambda *a,**k:Container())
 with pytest.raises(ConfigError,match='display rotation'):list(video.frame_generator(path,source_pts=True))

def processor(tmp_path):
 p=object.__new__(LayerBEventProcessor);p.config=load_frozen_config();p.cache_dir=tmp_path/'cache';p.cache_dir.mkdir();return p

def test_orientation_policy_separates_legacy_cache_and_rejects_legacy_provenance(tmp_path):
 p=processor(tmp_path);prov=p.build_stream_provenance(cohort='train_events',event_id='event_001',source_id='camera_1',modality='vision',run_id='generated:rotation',source_pts=True,video_stream_index=0)
 assert prov.preprocessing_config['orientation_policy']==video.SOURCE_DISPLAY_ROTATION_POLICY
 from dataclasses import replace
 old=replace(prov,preprocessing_config={k:v for k,v in prov.preprocessing_config.items()if k!='orientation_policy'})
 assert old.cache_key()!=prov.cache_key()
 with pytest.raises(CacheProvenanceError,match='orientation'):
  p.run_vision_inference(tmp_path/'not_opened.mov',tmp_path/'not_opened.pt','camera_1',source_pts=True,video_stream_index=0,provenance=old)

def test_actual_inference_handoff_uses_oriented_pixels_and_records_geometry(tmp_path):
 path=generated_rotated(tmp_path,-90);p=processor(tmp_path);shapes=[]
 def predict(image,**kwargs):shapes.append(image.shape);return []
 p._get_yolo_model=lambda _:SimpleNamespace(names={},predict=predict)
 result=p.run_vision_inference(path,tmp_path/'never_loaded.pt','camera_1',use_cache=False,source_pts=True,video_stream_index=0)
 assert len(result)==4 and all(shape==(80,48,3)for shape in shapes)
 restored=deserialize_evidence_record(serialize_evidence_record(result[0]))
 assert restored.metadata['display_rotation_degrees']==-90
 assert restored.metadata['input_image_size']==[48,80]
 assert restored.metadata['image_coordinate_basis']==video.SOURCE_DISPLAY_ROTATION_POLICY
 assert restored.metadata['pts_ticks']==result[0].metadata['pts_ticks']
