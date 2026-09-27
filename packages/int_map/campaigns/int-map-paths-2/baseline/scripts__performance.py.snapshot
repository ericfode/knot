#!/usr/bin/env python3
"""Build and time Bend workloads; correctness and structure counts stay in Bend."""
import json, pathlib, subprocess, time, platform
P=pathlib.Path(__file__).resolve().parents[1]; B=P.parents[1]/'scripts/bend-reference'
for entry in ['scaling','benchmark']:
 for suffix in ['', '.js']:
  subprocess.run([str(B),str(P/(entry+'.bend')),'-o',str(P/'build'/(entry+suffix))],check=True)
rows=[]
for n in [64,256,1024,4096]:
 for backend,cmd in [('native',[str(P/'build/benchmark')]),('javascript',['bun',str(P/'build/benchmark.js')])]:
  samples=[]
  for trial in range(3):
   t=time.perf_counter();r=subprocess.run(cmd+[str(n)],text=True,capture_output=True,check=True);samples.append(time.perf_counter()-t)
  rows.append(dict(n=n,backend=backend,seconds=samples,receipt=r.stdout))
 # Untimed quadratic independent list-model check, separately from core timing.
 for cmd in [[str(P/'build/scaling')],['bun',str(P/'build/scaling.js')]]:
  subprocess.run(cmd+[str(n)],text=True,capture_output=True,check=True)
 print(json.dumps(rows[-2:]),flush=True)
(P/'build/performance.json').write_text(json.dumps(dict(platform=platform.platform(),timing_scope='process startup, build, self-union, lookup validation, fold, size, full erasure; dense and 16-bit shared-prefix layouts; independent list oracle excluded',rows=rows),indent=2)+'\n')
