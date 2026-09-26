#!/usr/bin/env python3
"""Regression gate for benchmark input bounds; preserve published receipts."""
import hashlib,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parents[1];ROOT=P.parents[1];B=ROOT/'scripts/bend-reference'
BUILD=P/'build/perch-audit';BUILD.mkdir(parents=True,exist_ok=True)
OUT=P/'receipts/perch-audit-2026-09-26/scaling-after.json'
rows=[]
def record(name,cmd,expected=0):
 r=subprocess.run(list(map(str,cmd)),cwd=ROOT,text=True,capture_output=True,timeout=30)
 rows.append(dict(name=name,args=list(map(str,cmd)),exit=r.returncode,stdout=r.stdout,stderr=r.stderr))
 if r.returncode!=expected:raise AssertionError(rows[-1])
 return r
for entry in ['scaling','benchmark']:
 for backend,suffix,runner in [('native','',[]),('javascript','.js',['bun'])]:
  exe=BUILD/(entry+'-after'+suffix)
  record(entry+'_'+backend+'_build',[B,P/(entry+'.bend'),'-o',exe])
  for args in [[],['1'],['64'],['4096']]:
   r=record(entry+'_'+backend+'_valid',runner+[exe]+args)
   assert 'union_sum=' in r.stdout
  for args in [['0'],['4097'],['65537'],['4294967296'],['not-a-number']]:
   r=record(entry+'_'+backend+'_invalid',runner+[exe]+args,2)
   assert r.stdout=='' and 'expected positive size <=4096' in r.stderr
record('unchanged_release_proofs',[B,P/'PROOF.bend','--check-only'])
result=dict(source_sha256=hashlib.sha256((P/'scaling.bend').read_bytes()).hexdigest(),pass_=True,rows=rows)
OUT.write_text(json.dumps(result,indent=2)+'\n')
print('SCALING BOUNDS PASS: native/JS, both entries, 16 valid and 20 invalid runs; proofs pass.')
