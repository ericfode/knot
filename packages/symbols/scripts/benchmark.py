#!/usr/bin/env python3
import hashlib,json,os,pathlib,platform,statistics,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=ROOT/'packages/symbols'; BEND=ROOT/'scripts/bend-reference'
OUT=PKG/os.environ.get('SYMBOLS_RECEIPTS_DIR','receipts/working')
OUT.mkdir(parents=True,exist_ok=True)
(PKG/'build').mkdir(parents=True,exist_ok=True)
sources=[PKG/'benchmark.bend',PKG/'main.bend',ROOT/'packages/vec/main.bend']
before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
rows=[]
for n in [128,256,512]:
 for length in [0,64,256]:
  entry=PKG/f'build/bench_{n}_{length}.bend'; binary=entry.with_suffix('')
  entry.write_text(f'import Base\nimport ../benchmark.bend as B\ndef main() -> U32: B.repeated(16n,{n}n,B.prefix({length}n))\n')
  built=subprocess.run([str(BEND),str(entry),'-o',str(binary)],text=True,capture_output=True,timeout=120)
  assert built.returncode==0,built.stderr
  times=[]
  for trial in range(3):
   start=time.perf_counter(); r=subprocess.run([str(binary)],text=True,capture_output=True,timeout=120); times.append(time.perf_counter()-start)
   assert r.returncode==0 and r.stdout.strip()=='0',(r.stdout,r.stderr)
  rows.append({'distinct_names':n,'extra_common_prefix_codepoints':length,'repetitions':16,'intern_calls':32*n,'resolve_calls':16*n,'errors':0,'seconds':times,'median_seconds':statistics.median(times)})
assert {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}==before,'source changed during benchmark'
receipt={'checked_inputs_sha256':before,'platform':platform.platform(),'machine':platform.machine(),'benchmark_sha256':hashlib.sha256((PKG/'benchmark.bend').read_bytes()).hexdigest(),'lane':'native CPU','measure':'wall time including process start; 3 trials, 16 complete tables per process','allocation_counts':'not instrumented','rows':rows}
(OUT/'benchmark.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(rows,indent=2))
