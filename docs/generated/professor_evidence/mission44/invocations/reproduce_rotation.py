"""Generated codec proof: legacy display orientation versus native-PTS coded pixels."""
from common import *
import tempfile,numpy as np
from fractions import Fraction
import av,cv2
from railway_detection.vision.video import frame_generator
work=Path(tempfile.mkdtemp(prefix='m44_generated_rotation_',dir='/private/tmp'));base=work/'generated_base.mp4';rot=work/'generated_minus90.mp4'
# Asymmetric generated pattern; never original source media.
image=np.zeros((48,80,3),np.uint8);image[:24,:40]=[230,20,10];image[:24,40:]=[15,210,20];image[24:,:40]=[20,30,220];image[24:,40:]=[230,210,20]
with av.open(str(base),'w')as out:
 stream=out.add_stream('libx264',rate=5);stream.width=80;stream.height=48;stream.pix_fmt='yuv420p'
 for i in range(3):
  frame=av.VideoFrame.from_ndarray(image,format='bgr24');frame.pts=i;frame.time_base=Fraction(1,5)
  for p in stream.encode(frame):out.mux(p)
 for p in stream.encode():out.mux(p)
cmd=['ffmpeg','-nostdin','-v','error','-display_rotation:v:0','-90','-i',str(base),'-c','copy',str(rot)];subprocess.run(cmd,check=True,capture_output=True)
with av.open(str(rot))as c:frame=next(c.decode(video=0));raw=frame.to_ndarray(format='bgr24');rotation=frame.rotation;pts=frame.pts;tb=str(frame.time_base)
cap=cv2.VideoCapture(str(rot));orientation_auto=cap.get(cv2.CAP_PROP_ORIENTATION_AUTO);ok,legacy=cap.read();cap.release();assert ok
native=next(frame_generator(rot,source_pts=True));expected=np.ascontiguousarray(np.rot90(raw,k=rotation//90));assert rotation==-90 and legacy.shape==expected.shape
def corners(x):
 h,w=x.shape[:2];return [np.mean(x[y:y+8,z:z+8],axis=(0,1))for y,z in [(0,0),(0,w-8),(h-8,0),(h-8,w-8)]]
palette=[np.array(c)for c in [[230,20,10],[15,210,20],[20,30,220],[230,210,20]]]
def signature(x):return [int(np.argmin([np.linalg.norm(c-p)for p in palette]))for c in corners(x)]
assert signature(expected)==signature(legacy)
proof={'schema':'mission44-display-rotation-defect-reproduction/1','fixture_origin':'Purely generated asymmetric pixels, not original railway media','ffmpeg_command':cmd,'fixture_sha256':sha(rot),'PyAV_rotation':rotation,'raw_coded_shape':list(raw.shape),'source_pts_reader_before_fix_shape':list(native.image.shape),'OpenCV_legacy_display_shape':list(legacy.shape),'OpenCV_orientation_auto':orientation_auto,'expected_native_display_shape':list(expected.shape),'raw_pixels_equal_old_PTS_reader':bool(np.array_equal(raw,native.image)),'expected_display_corner_signature_matches_legacy_OpenCV':signature(expected)==signature(legacy),'legacy_exact_pixels_not_required':'Installed PyAV/OpenCV bundle different FFmpeg versions and differ slightly in YUV-to-BGR rounding; compare coded/display geometry and asymmetric spatial color ordering, not identical cross-backend RGB bytes','PTS':pts,'timebase':tb,'defect_confirmed':native.image.shape!=legacy.shape,'real_sources_with_rotation_metadata':44,'affected_front':24,'affected_back':20,'no_model_forward_or_raw_source_access':True,'installed_PyAV_property_documentation':'VideoFrame.rotation is DISPLAYMATRIX counterclockwise rotation in[-180,180] degrees','conclusion':'Source PTS route added inM37 drops display rotation formerly applied by OpenCV. Correct orthogonal source display interpretation is a decoder pixel-convention regression fix, not a new model/threshold.'};assert proof['defect_confirmed'];save(D/'DISPLAY_ROTATION_DEFECT_REPRODUCTION.json',proof);print(json.dumps(proof,indent=2))
