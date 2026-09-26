#!/usr/bin/env python3
"""Build orchestration only: all semantics and unchanged assertions are Bend."""
from pathlib import Path
import json, subprocess, shutil, time
ROOT=Path(__file__).resolve().parents[3]
PKG=ROOT/'packages/term_store'
BEND=ROOT/'scripts/bend-reference'
base=(PKG/'main.bend').read_text()
mutants=[
 ('allocation-stale-id','Done{Id{scope,slot}}','Done{Id{scope,U32.add(slot,1)}}','store-values-growth-update-preservation'),
 ('update-wrong-slot','V.Vec.set(T,v,i,x)','V.Vec.set(T,v,0,x)','store-values-growth-update-preservation'),
 ('accept-foreign-scope','get_scoped(T,k,v,i,U32.is_eq(k,j))','get_scoped(T,k,v,i,True{})','store-values-growth-update-preservation'),
 ('scope-reuse','Scopes{U32.add(next,1),True{}}','Scopes{next,True{}}','lifetime-separation'),
 ('scope-exhaustion-wrap','(Scopes{next,False{}},Done{next})','(Scopes{0,True{}},Done{next})','scope-exhaustion'),
 ('finish-before-begin','case Succeed{x}:\n          (Pending{},Fail{InvalidTransition{}})','case Succeed{x}:\n          (Ready{x},Done{Unit{}})','memo-transition-result-preservation'),
 ('cancel-remains-evaluating','case Cancel{}:\n          (Pending{},Done{Unit{}})','case Cancel{}:\n          (Evaluating{},Done{Unit{}})','memo-transition-result-preservation'),
 ('terminal-false-success','(Ready{x},Fail{InvalidTransition{}})','(Ready{x},Done{Unit{}})','memo-transition-result-preservation'),
 ('completed-value-discarded','case Ready{x}:\n      Done{Done{x}}','case Ready{x}:\n      Fail{NotReady{}}','first-order-term-payloads'),
 ('memo-success-without-write','memo_wrap(T,E,Unit,Store.set(Cell<T,E>,s,id,cell))','(Memo{s},Done{Unit{}})','first-order-term-payloads'),
]
out=[]
for name,old,new,expected in mutants:
 assert base.count(old)==1,(name,base.count(old))
 work=PKG/'.build/mutants'/name
 work.mkdir(parents=True,exist_ok=True)
 # Dependency remains a reference. Never copy Vec or sibling implementation.
 for src in PKG.glob('*.bend'):
  text=src.read_text()
  if src.name=='main.bend': text=text.replace(old,new)
  text=text.replace('import ../vec/main.bend as V',f'import {ROOT}/packages/vec/main.bend as V')
  (work/src.name).write_text(text)
 def call(args):
  start=time.monotonic();p=subprocess.run([str(x) for x in args],cwd=ROOT,text=True,capture_output=True,timeout=120)
  return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start}
 receipt={'name':name,'witness_group':expected,'before':old,'after':new}
 receipt['typecheck']=call([BEND,work/'main.bend','--check-only'])
 if receipt['typecheck']['exit']!=0: raise RuntimeError(receipt)
 receipt['compile']=call([BEND,work/'conformance.bend','-o',work/'run'])
 if receipt['compile']['exit']!=0: raise RuntimeError(receipt)
 receipt['assertion']=call([work/'run'])
 receipt['semantic_kill']=receipt['assertion']['exit']==1 and f'FAIL {expected}' in receipt['assertion']['stderr']
 out.append(receipt)
 print(name,receipt['semantic_kill'],flush=True)
 if not receipt['semantic_kill']: raise RuntimeError(receipt)
(PKG/'evidence/mutations.json').write_text(json.dumps(out,indent=2)+'\n')
