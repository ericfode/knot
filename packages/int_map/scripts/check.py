#!/usr/bin/env python3
"""Reproduce the deterministic law-quality gates without publishing."""
import datetime, hashlib, json, pathlib, shutil, subprocess, time
P=pathlib.Path(__file__).resolve().parents[1];ROOT=P.parents[1];B=ROOT/'scripts/bend-reference'
(P/'build').mkdir(exist_ok=True);(P/'receipts').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_hashes():return {str(p.relative_to(P)):sha(p) for p in sorted(P.glob('*.bend'))}|{'LICENSE':sha(P/'LICENSE')}
before=source_hashes();steps=[]
def run(name,args):
 t=time.perf_counter();r=subprocess.run(list(map(str,args)),cwd=ROOT,text=True,capture_output=True)
 row=dict(name=name,args=list(map(str,args)),exit=r.returncode,seconds=time.perf_counter()-t,stdout=r.stdout,stderr=r.stderr);steps.append(row)
 (P/'receipts/gates.json').write_text(json.dumps(dict(source_sha256=before,steps=steps),indent=2)+'\n')
 if r.returncode:raise RuntimeError(name+' failed: '+r.stdout+r.stderr)
 print(name+' PASS',flush=True)
run('proof',[B,P/'PROOF.bend','--check-only'])
run('release_check',[B,P/'release.bend','--check-only'])
for backend,ext,runner in [('native','',[]),('javascript','.js',['bun'])]:
 target=P/'build'/('release'+ext)
 run(backend+'_build',[B,P/'release.bend','-o',target])
 run(backend+'_run',runner+[target])
run('semantic_mutants',['python3',P/'scripts/mutations.py'])
run('scaling',['python3',P/'scripts/performance.py'])
run('exact_closure',['bun',P/'scripts/inspect-release.ts'])
assert before==source_hashes(),'sources changed during gates'
for name in ['closure','mutations','performance']:shutil.copy2(P/'build'/(name+'.json'),P/'receipts'/(name+'.json'))
summary=dict(date=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=before,steps=steps,deterministic_pass=True,proof_holes=0,gpu_validated=False)
(P/'receipts/gates.json').write_text(json.dumps(summary,indent=2)+'\n')
print('DETERMINISTIC GATES PASS',flush=True)
