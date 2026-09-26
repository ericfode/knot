"""Serialize reviewed source/ABI observations; never derive expectations from Knot."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
previous=json.loads((ROOT/'tests/compiler-checker/cases.json').read_text())
cases=[]
for c in previous['cases']:
 if c['knot']['exit']==0:
  cases.append({'file':c['file'],'type':'Flag','type_id':0,'constructors':['Off','On'],'calls':[{'export':'main','arguments':[],'tag':1,'seed':'F.main()'}]})

def get(name):return next(c for c in cases if Path(c['file']).stem==name)
def call(name,export,args,tag,seed): get(name)['calls'].append({'export':export,'arguments':args,'tag':tag,'seed':seed})
for x in (0,1):
 ctor=['Off','On'][x]
 for name,fn,tag in [('flag','flip',1-x),('renamed','toggle',1-x),('reordered-arms','flip',1-x),('matched-return','f',x),('matched-duplicate','f',x),('data-argument','f',x),('data-promote','f',x),('data-reuse','reuse',x),('erased-affine-copy','f',x)]:
  call(name,fn,[x],tag,f'F.{fn}(F.{ctor}{{}})')
 call('shadowing','shadow',[x],1,f'F.shadow(F.{ctor}{{}})')
 call('erased-forward','take',[x],x,f'F.take(F.Off{{}},F.{ctor}{{}})')
for a in (0,1):
 for b in (0,1):
  ca=['Off','On'][a];cb=['Off','On'][b]
  call('nested-match','both',[a,b],1-b if a==0 else b,f'F.both(F.{ca}{{}},F.{cb}{{}})')
  call('branch-maximum','f',[a,b],b,f'F.f(F.{ca}{{}},F.{cb}{{}})')
  call('duplicate-parameters','f',[a,b],b,f'F.f(F.{ca}{{}},F.{cb}{{}})')

def fixture(name,type_name,type_id,constructors,main_tag):
 cases.append({'file':f'tests/compiler-wasm/fixtures/{name}.bend','type':type_name,'type_id':type_id,'constructors':constructors,'calls':[{'export':'main','arguments':[],'tag':main_tag,'seed':'F.main()'}]})
fixture('three-colors','Color',0,['Red','Green','Blue'],2)
fixture('mixed-types','Color',1,['Red','Green','Blue'],1)
fixture('branch-locals','Flag',0,['Off','On'],0)
fixture('erased-cost','Flag',0,['Off','On'],1)
fixture('argument-order','Flag',0,['Off','On'],0)
fixture('high-tags','Tag',0,[f'T{i}' for i in range(256)],255)
fixture('high-function-index','Flag',0,['Off','On'],1)
fixture('high-local-index','Flag',0,['Off','On'],1)
for n in (0,1,2):
 color=['Red','Green','Blue'][n]
 call('three-colors','cycle',[n],(n+1)%3,f'F.cycle(F.{color}{{}})')
 for x in (0,1):
  ctor=['Off','On'][x]
  call('mixed-types','choose',[x,n],n if x==0 else 2,f'F.choose(F.Off{{}},F.{ctor}{{}},F.{color}{{}})')
for a in (0,1):
 for b in (0,1):
  ca=['Off','On'][a];cb=['Off','On'][b]
  call('branch-locals','f',[a,b],b if a==0 else 1,f'F.f(F.{ca}{{}},F.{cb}{{}})')
  call('argument-order','first',[a,b],a,f'F.first(F.{ca}{{}},F.On{{}},F.{cb}{{}})')
  call('argument-order','second',[a,b],b,f'F.second(F.{ca}{{}},F.Off{{}},F.{cb}{{}})')
for n in (0,63,64,127,128,255):call('high-tags','identity',[n],n,f'F.identity(F.T{n}{{}})')
call('high-tags','signed_edge',[],64,'F.signed_edge()')
call('high-function-index','f128',[],1,'F.f128()')
call('high-local-index','pick',[0]*128+[1],1,'F.pick('+','.join(['F.Off{}']*128+['F.On{}'])+')')
call('high-local-index','pick',[1]*128+[0],0,'F.pick('+','.join(['F.On{}']*128+['F.Off{}'])+')')
(HERE/'cases.json').write_text(json.dumps({'profile':'knot-enum-1','host':'Node 22.22.3 macOS arm64','cases':cases},indent=2)+'\n')
