#!/usr/bin/env python3
"""Portable package-only verification. Never opens raw media, models or repository originals."""
from pathlib import Path
from fractions import Fraction
import collections,csv,gzip,hashlib,io,json,re,sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
PREFIX='docs/generated/professor_evidence/mission43/'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(name):
 p=ROOT/name
 if p.is_symlink()or not p.resolve().is_relative_to(ROOT):raise ValueError('Nonlocal/symlink package artifact: '+name)
 return p

def verify():
 index={}
 for line in (ROOT/'PACKAGE_FILES.sha256').read_text().splitlines():
  value,name=line.split('  ',1)
  if name in index or not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('Invalid/duplicate index entry')
  index[name]=value
 actual={str(p.relative_to(ROOT))for p in ROOT.rglob('*')if p.is_file()}
 if actual!=set(index)|{'PACKAGE_FILES.sha256'}:raise ValueError('Missing or extra package files')
 for name,value in index.items():
  if digest(local(name))!=value:raise ValueError('Checksum mismatch: '+name)
 with(ROOT/'EVIDENCE_MANIFEST.csv').open(newline='')as f:manifest=list(csv.DictReader(f))
 names=[r['package_location']for r in manifest]
 if len(set(names))!=len(names)or set(names)!=set(index)-{'EVIDENCE_MANIFEST.csv'}:raise ValueError('Manifest/index coverage differs')
 for row in manifest:
  if row['sha256']!=digest(local(row['package_location']))or not all(row.values()):raise ValueError('Invalid manifest row')
  if row['artifact_kind']=='COPIED_ORIGINAL'and row['sha256']!=row['original_sha256']:raise ValueError('Copied original identity mismatch')
 copies=json.loads((ROOT/'COPIED_EVIDENCE_SOURCE_MAP.json').read_text())
 def resolve(reference):
  if reference.startswith(PREFIX):return local(reference[len(PREFIX):])
  if reference in copies:return local(copies[reference]['package_path'])
  raise ValueError('Referenced payload not packaged: '+reference)
 def artifact(ref):
  p=resolve(ref['path'])
  if digest(p)!=ref['sha256']:raise ValueError('Actual output payload hash mismatch')
  rows=[json.loads(line)for line in p.read_text().splitlines()]
  if len(rows)!=ref['records']:raise ValueError('Actual output row count differs')
  return rows
 parsed=collections.Counter();links=0
 for name in index:
  p=local(name)
  if p.suffix=='.json':json.loads(p.read_text());parsed['json']+=1
  elif p.suffix=='.jsonl':
   for line in p.read_text().splitlines():
    if line.strip():json.loads(line)
   parsed['jsonl']+=1
  elif p.suffix=='.csv':
   rows=list(csv.reader(io.StringIO(p.read_text())))
   if not rows or len(set(rows[0]))!=len(rows[0])or any(len(r)!=len(rows[0])for r in rows):raise ValueError('CSV structure: '+name)
   parsed['csv']+=1
  elif p.suffix=='.xml'or p.name.endswith('.xml.gz'):ET.fromstring(gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes());parsed['xml']+=1
  elif p.suffix=='.gz':gzip.decompress(p.read_bytes());parsed['other_gzip']+=1
  if p.suffix=='.md'and '/'not in name:
   for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)',p.read_text()):
    target=target.strip().strip('<>')
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target)or target.startswith('#'):continue
    if not local(target.split('#',1)[0]).is_file():raise ValueError('Broken current-report link: '+name+':'+target)
    links+=1
 visual=json.loads((ROOT/'ACTUAL_VISUAL_RUN_MANIFEST.json').read_text());audio=json.loads((ROOT/'ACTUAL_AUDIO_RUN_MANIFEST.json').read_text());totals=collections.Counter();sources=json.loads((ROOT/'SOURCE_VERIFICATION_RECEIPT.json').read_text());assert sources['verified']==54 and sources['failed']==0
 assert len({x['fresh_sha256']for x in sources['members']})==54
 for e in visual['events']:
  assert e['status']in ['COMPLETED_ORIGINAL_INFERENCE','REUSED_MISSION39_ACTUAL_INFERENCE']
  rows=artifact(e['predictions']);totals[e['camera']+'_records']+=len(rows);totals[e['camera']+'_objects']+=sum(len(r['detections'])for r in rows)
  for r in rows:
   m=r['metadata'];assert m['timestamp_basis']=='source_pts';assert float(Fraction(m['pts_ticks'])*Fraction(*m['timebase']))==r.get('timestamp_sec',r.get('timestamp_s'))
 for e in audio['events']:
  assert e['status']in ['COMPLETED_ORIGINAL_AUDIO_INFERENCE','REUSED_MISSION39_CORRECTED_AUDIO']
  rows=artifact(e['predictions']);artifact(e['clock_ledger']);artifact(e['descriptive_cache_rows']);assembled=artifact(e['B2_input_assembly']);totals['audio_windows']+=len(rows);totals['audio_positive_windows']+=sum(r['metadata']['probability']>=.37 for r in rows);totals['B2_input_frames']+=len(assembled);totals['B2_both_record_frames']+=sum(bool(r['front_prediction_timestamps'])and bool(r['causal_audio_window_end_timestamps'])for r in assembled)
  assert all(r['metadata']['feature_log_scale']=='natural'for r in rows)
 assert dict(totals)=={'front_records':6613,'front_objects':329,'back_records':6479,'back_objects':1020,'audio_windows':2600,'audio_positive_windows':445,'B2_input_frames':6614,'B2_both_record_frames':3897},totals
 m=json.loads((ROOT/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json').read_text());assert m['actual_event_denominator']==23 and m['confusion_matrix']=={'tp':12,'fp':10,'fn':1,'tn':0};assert m['scope_sha256']==digest(ROOT/'EVALUATION_SCOPE_FREEZE.md')
 for phase in ['verification','vision','audio']:
  for state in ['ISSUED','CLOSED']:
   x=json.loads((ROOT/'operations'/f'{phase}_{state}_AUTHORIZATION.json').read_text());assert x['bindings']['protocol_document']['sha256']==digest(ROOT/'EXECUTION_SCOPE.md');seal=hashlib.sha256(json.dumps({k:v for k,v in x.items()if k!='record_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest();assert seal==x['record_sha256']
 for name,meta in [('verify_sources.py',sources),('run_vision.py',visual),('run_audio.py',audio)]:assert digest(ROOT/'invocations'/name)==meta['invocation_sha256']
 tests=collections.Counter();ids=[]
 for p in(ROOT/'software_validation/groups').glob('*/pytest.xml.gz'):
  for c in ET.fromstring(gzip.decompress(p.read_bytes())).iter('testcase'):
   ids.append((c.get('classname'),c.get('name')));tests['errors'if c.find('error')is not None else'failures'if c.find('failure')is not None else'skipped'if c.find('skipped')is not None else'passed']+=1
 assert len(ids)==len(set(ids))==3815 and dict(tests)=={'passed':3700,'failures':84,'errors':31}
 follow=list(ET.parse(ROOT/'software_validation/READ_ONLY_DATA_INTEGRATION.xml').iter('testcase'));assert len(follow)==15 and all(not len(c)for c in follow)
 fig=json.loads((ROOT/'FIGURE_PROVENANCE.json').read_text());assert digest(ROOT/'invocations/plot_results.py')==fig['plotting_script_sha256']
 for item in fig['figures']:
  assert digest(resolve(item['figure']))==item['sha256']
  for name,value in item['input_tables'].items():assert digest(local(name))==value
 return {'valid':True,'files':len(actual),'manifest_entries':len(manifest),'checksummed_files':len(index),'current_report_local_links':links,'parsed':dict(parsed),'actual_output_totals':dict(totals),'full_guarded_tests':{'tests':3815,**dict(tests),'skipped':0},'separate_metadata_integration_passed':15,'scope_and_invocation_bindings_valid':True,'package_only_no_raw_media_models_repository_or_network':True}
if __name__=='__main__':
 try:print(json.dumps(verify(),indent=2))
 except (OSError,ValueError,KeyError,AssertionError,ET.ParseError)as exc:
  print('Package verification failed: '+str(exc),file=sys.stderr);sys.exit(1)
