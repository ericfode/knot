#!/usr/bin/env python3
"""Reproducible local gates. Semantics/oracles remain in Bend."""
from pathlib import Path
import subprocess,json,time,hashlib,platform
ROOT=Path(__file__).resolve().parents[3]; PKG=ROOT/'packages/term_store';BEND=ROOT/'scripts/bend-reference'
(PKG/'.build').mkdir(exist_ok=True)
receipt={'compiler':'Bend 2.0.29','revision':'574b6d39a235b539eb19a5c532993a0abb3d11ad','host':platform.platform(),'gates':[]}
def run(name,args,expected=0,contains=None,timeout=600):
 t=time.monotonic();p=subprocess.run([str(a) for a in args],cwd=ROOT,capture_output=True,text=True,timeout=timeout)
 row={'name':name,'expected_exit':expected,'expected_diagnostic':contains,'command':[str(a) for a in args],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t}
 receipt['gates'].append(row)
 (PKG/'evidence/gates.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert p.returncode==expected,(name,row)
 if contains: assert contains in p.stdout+p.stderr,(name,row)
 print(name,'PASS',round(row['seconds'],3),flush=True)
run('complete-proof-zero-holes',[BEND,PKG/'PROOF.bend','--check-only'],contains='All terms check.')
for target,cmd in [('native',[]),('javascript',['bun'])]:
 output=PKG/'.build'/('conformance'+('.js' if cmd else ''))
 run(target+'-compile',[BEND,PKG/'conformance.bend','-o',output])
 run(target+'-conformance',cmd+[output],contains='PASS 128-mixed-histories-x128-operations')
for name,diagnostic in [('duplicate_store','consumed more than once'),('duplicate_memo','consumed more than once'),('closure_payload','- expected : Data\n- observed : Type')]:
 run('negative-'+name,[BEND,PKG/'tests/negative'/f'{name}.bend','--check-only'],expected=1,contains=diagnostic)
run('semantic-mutations',['python3',PKG/'scripts/mutations.py'])
receipt['negative_source_sha256']={str(p.relative_to(PKG)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((PKG/'tests/negative').glob('*.bend'))}
receipt['source_sha256']={str(p.relative_to(PKG)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PKG.glob('*.bend'))}
(PKG/'evidence/gates.json').write_text(json.dumps(receipt,indent=2)+'\n')
