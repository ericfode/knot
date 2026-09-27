"""Paired 4096-entry baseline/candidate timing; assertions stay in frozen Bend."""
import hashlib,json,pathlib,shutil,statistics,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[4]
P=ROOT/'packages/int_map'; O=pathlib.Path(__file__).resolve().parent
B=P/'build/int-map-paths-1/comparison'; B.mkdir(parents=True,exist_ok=True)
pre=json.loads((O/'preregistration.json').read_text())
commands={}
for version in ['baseline','candidate']:
 d=B/version; d.mkdir(exist_ok=True)
 for name in [name for name in pre['baseline_sha256'] if name.endswith('.bend')]:
  source=O/'baseline'/(name+'.snapshot') if version=='baseline' else P/name
  data=source.read_bytes()
  if version=='baseline' or name!='main.bend':
   assert hashlib.sha256(data).hexdigest()==pre['baseline_sha256'][name]
  (d/name).write_bytes(data)
 for backend,suffix,runner in [('native','',[]),('javascript','.js',['bun'])]:
  exe=d/('run'+suffix)
  subprocess.run([str(ROOT/'scripts/bend-reference'),str(d/'benchmark.bend'),'-o',str(exe)],check=True)
  commands[version,backend]=runner+[str(exe),'4096']
rows=[]
for backend in ['native','javascript']:
 expected=None
 for version in ['baseline','candidate']:
  r=subprocess.run(commands[version,backend],capture_output=True,text=True,check=True)
  if expected is None: expected=r.stdout
  assert r.stdout==expected
 samples={v:[] for v in ['baseline','candidate']}
 for trial in range(5):
  for v in (['baseline','candidate'] if trial%2==0 else ['candidate','baseline']):
   start=time.perf_counter();r=subprocess.run(commands[v,backend],capture_output=True,text=True,check=True)
   samples[v].append(time.perf_counter()-start);assert r.stdout==expected
 med={v:statistics.median(s) for v,s in samples.items()}
 rows.append(dict(backend=backend,n=4096,seconds=samples,median_seconds=med,candidate_over_baseline=med['candidate']/med['baseline'],identical_stdout=expected))
result=dict(scope='Descriptive paired process timings, one warmup per version/backend and five alternating samples; startup and full dense/shared-prefix workload included; concurrent machine; no speedup or universal nonregression claim',rows=rows)
(O/'performance-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
for row in rows:print(row['backend'],row['median_seconds'],row['candidate_over_baseline'])
