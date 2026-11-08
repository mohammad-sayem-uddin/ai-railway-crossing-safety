"""Full inherited guarded audit; persist completed group logs and timings immediately."""
from pathlib import Path
import gzip,json,shutil,tempfile,threading,time
from scripts.run_resource_free_acceptance import execute
from railway_detection.safety.resource_free_acceptance import inventory
R=Path.cwd();D=R/'docs/generated/research_results/mission40/software_validation';out=Path(tempfile.mkdtemp(prefix='m40_final_',dir='/private/tmp'));done=threading.Event();lock=threading.Lock()
Path('/private/tmp/m40_final_path').write_text(str(out))
def preserve():
 with lock:
  p=out/'receipt.json'
  if not p.exists():return
  try:body=p.read_bytes();receipt=json.loads(body)
  except (OSError,ValueError):return
  for group in receipt['groups']:
   destination=D/'groups'/group['group'];destination.mkdir(parents=True,exist_ok=True)
   for name in ['pytest.xml','stdout.txt','stderr.txt','policy_denials.jsonl','collected.json']:
    source=out/group['group']/name
    if source.exists():
     target=destination/(name+'.gz')
     if not target.exists():target.write_bytes(gzip.compress(source.read_bytes(),mtime=0))
  (D/'FULL_RUN_RECEIPT.json').write_bytes(body)
def monitor():
 while not done.wait(2):preserve()
thread=threading.Thread(target=monitor,daemon=True);started=time.perf_counter();thread.start()
try:execute(out,inventory(R),audit=True,exclusions={})
finally:
 done.set();thread.join();preserve()
 (D/'FULL_RUN_WALL_TIME.json').write_text(json.dumps(dict(elapsed_wall_s=time.perf_counter()-started,clock='time.perf_counter',includes_orchestration=True,reason_for_rerun='Completed earlier receipt survived interruption, but temporary JUnit/timing evidence did not; retain all completed group artifacts incrementally',prior_completed_receipt='COMPLETED_PRE_RESUMPTION_RUN_RECEIPT.json'),indent=2)+'\n')
print(str(out))
