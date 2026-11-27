from pathlib import Path
import csv,json,collections
ROOT=Path(__file__).resolve().parents[1]
reports=[]
for folder,n,reps in [('data',16000000,9),('runs/atomic/data',1000000,7),('runs/matched_store/data',1000000,7)]:
 base=ROOT/folder
 raw=list(csv.DictReader(open(base/'raw.csv')))
 addresses=collections.defaultdict(list)
 for r in csv.DictReader(open(base/'addresses.csv')):addresses[int(r['order'])].append(r)
 cells=collections.defaultdict(list)
 measured_started=False
 for order,r in enumerate(raw):
  assert int(r['order'])==order
  t=int(r['threads']);stride=int(r['stride']);batch=int(r['batch']);rep=int(r['rep'])
  assert r['correct']==r['affinity_ok']==r['aligned_ok']=='1'
  assert float(r['seconds'])>0
  assert int(r['storage_bytes'])==t*stride
  assert int(r['updates_per_thread'])==(n+batch-1)//batch
  if rep>=0:measured_started=True
  else:assert not measured_started
  cells[(r['placement'],t,batch,stride)].append(rep)
  aa=addresses[order];assert len(aa)==t
  first=int(aa[0]['address']);assert first%64==0
  expected={'P_physical':[0,2,4,6,8,10],'P_SMT':list(range(12)),'E_physical':[12,13,14,15]}[r['placement']][:t]
  for i,a in enumerate(aa):
   address=int(a['address'])
   assert int(a['thread'])==i and int(a['cpu'])==expected[i]
   assert address==first+i*stride
   assert int(a['offset'])==address%64 and int(a['line_index'])==address//64
  if stride==64:assert len({a['line_index']for a in aa})==t
 assert len(cells)==88
 assert all(sorted(v)==list(range(-1,reps))for v in cells.values())
 reports.append(dict(dataset=folder,conditions=len(cells),executions=len(raw),measured=88*reps,address_records=sum(map(len,addresses.values())),all_checks_passed=True))
result=dict(datasets=reports,total_executions=sum(r['executions']for r in reports),total_measured=sum(r['measured']for r in reports),total_addresses=sum(r['address_records']for r in reports))
(ROOT/'data/validation_all.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
