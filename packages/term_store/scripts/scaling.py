#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,time,statistics,platform,hashlib
ROOT=Path(__file__).resolve().parents[3];p=ROOT/'packages/term_store'; bend=ROOT/'scripts/bend-reference'
for suffix in ['', '.js', '.c']:
 subprocess.run([str(bend),str(p/'benchmark.bend'),'-o',str(p/'.build'/('benchmark'+suffix))],cwd=ROOT,check=True)
rows=[]
for target,cmd in [('native',[str(p/'.build/benchmark')]),('javascript',['bun',str(p/'.build/benchmark.js')])]:
 for n in [16384,32768,65536,131072,262144,524288]:
  times=[]
  for _ in range(3):
   start=time.perf_counter();r=subprocess.run(cmd+[str(n)],text=True,capture_output=True,timeout=30);elapsed=time.perf_counter()-start
   assert r.returncode==0 and r.stdout.strip()==f'PASS n={n}',(cmd,n,r)
   times.append(elapsed)
  row={'target':target,'n':n,'seconds':times,'median_seconds':statistics.median(times),'public_alloc_calls':n,'public_get_calls':n,'expected_vec_growth_copied_slots':n-1,'growth_count':n.bit_length()-1,'verified':'all IDs scope 0 and slot i; all read values i'}
  rows.append(row);print(target,n,round(row['median_seconds'],4),flush=True)
(p/'evidence/scaling.json').write_text(json.dumps({'host':platform.platform(),'counts_kind':'source-derived exact counts for power-of-two n; not instrumented heap metrics','source_sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ['main.bend','benchmark.bend']},'rows':rows},indent=2)+'\n')
