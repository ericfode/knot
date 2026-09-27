#!/usr/bin/env python3
"""Generate fixed inputs, build Bend lanes and compare observations; no store semantics."""
from pathlib import Path
import datetime, gzip, hashlib, itertools, json, shutil, subprocess, time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = ROOT / '.local/owned-store'
RECEIPTS = HERE / 'receipts'
SEED = ROOT / 'scripts/bend-reference'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def run(argv, timeout=60):
    start = time.monotonic()
    try:
        p = subprocess.run(list(map(str, argv)), cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return dict(argv=list(map(str, argv)), exit=p.returncode, stdout=p.stdout, stderr=p.stderr,
                    elapsed_seconds=time.monotonic()-start)
    except subprocess.TimeoutExpired:
        return dict(argv=list(map(str, argv)), exit=None, status='harness-timeout', elapsed_seconds=time.monotonic()-start)

def require(test, detail):
    if not test: raise AssertionError(str(detail)[:1800])

def command(op):
    if op[0] == 'put': return f'P.Insert{{{op[1]},{op[2]}}}'
    if op[0] == 'alloc': return f'P.Reserve{{{op[1]}}}'
    tag = {'take':'Extract', 'drop':'Dispose'}[op[0]]
    return f'P.{tag}{{S.Locator{{{op[1]},{op[2]},{op[3]}}}}}'

def inputs():
    # Literal witnesses constrain the shared observation format and both lanes.
    cases = [
      ('zero',41,0,1,[('alloc',7)], '[fail:full:7]/41;0;1;[];[]'),
      ('occupied',41,1,1,[('put',0,7),('put',0,9)], '[alloc:41,0,0, fail:occupied:9]/41;1;1;[];[live:0:7]'),
      ('take-twice',41,1,1,[('alloc',7),('take',41,0,0),('take',41,0,0)], '[alloc:41,0,0, take:7, fail:stale:-]/41;1;1;[0];[free:1]'),
      ('retired-full',41,1,0,[('alloc',7),('drop',41,0,0),('alloc',9)], '[alloc:41,0,0, drop:7, fail:full:9]/41;1;0;[];[retired]'),
      ('wrong-arena-precedes-bounds',41,1,1,[('take',42,4294967295,4294967295)], '[fail:arena:-]/41;1;1;[0];[free:0]'),
      ('padding-is-not-a-slot',41,3,1,[('put',3,9)], '[fail:bounds:9]/41;3;1;[0, 1, 2];[free:0, free:0, free:0]'),
      ('unrelated-owner',41,2,1,[('alloc',7),('alloc',9),('drop',41,0,0)], '[alloc:41,0,0, alloc:41,1,0, drop:7]/41;2;1;[0];[free:1, live:0:9]'),
      ('free-order',41,3,1,[('alloc',7),('alloc',9),('take',41,0,0)], '[alloc:41,0,0, alloc:41,1,0, take:7]/41;3;1;[0, 2];[free:1, live:0:9, free:0]'),
      ('retirement-cycle',41,1,1,[('alloc',7),('take',41,0,0),('alloc',9),('take',41,0,1),('put',0,11)], '[alloc:41,0,0, take:7, alloc:41,0,1, take:9, fail:retired:11]/41;1;1;[];[retired]'),
      ('drop-vacant',41,1,1,[('drop',41,0,0)], '[fail:vacant:-]/41;1;1;[0];[free:0]'),
      ('oversized',41,4097,1,[], 'new:limit'),
      ('u32-capacity',41,4294967295,1,[], 'new:limit'),
      ('u32-index',41,1,1,[('put',4294967295,7),('take',41,4294967295,0)], '[fail:bounds:7, fail:bounds:-]/41;1;1;[0];[free:0]'),
      ('u32-arena',4294967295,1,4294967295,[('alloc',7),('take',4294967295,0,0)], '[alloc:4294967295,0,0, take:7]/4294967295;1;4294967295;[0];[free:1]'),
      ('stale-after-reuse',41,1,1,[('alloc',7),('take',41,0,0),('alloc',9),('take',41,0,0)], '[alloc:41,0,0, take:7, alloc:41,0,1, fail:stale:-]/41;1;1;[];[live:1:9]'),
    ]
    alphabet = [('alloc',7),('alloc',9),('put',1,11),('take',41,0,0),('take',41,0,1),
                ('drop',41,1,0),('take',42,0,0),('take',41,2,0)]
    for capacity, ceiling, length in itertools.product(range(3),range(2),range(4)):
        for ops in itertools.product(alphabet,repeat=length):
            cases.append(('exhaustive',41,capacity,ceiling,list(ops),None))
    for capacity in (3,4,16,64,256,1024,4096):
        cases.append(('capacity',41,capacity,1,[('put',capacity-1,9),('take',41,capacity-1,0)],None))
    return cases

def entry(folder, cases):
    rows=[]
    for i, (_,arena,capacity,ceiling,ops,_) in enumerate(cases):
        rows.append(f'P.Case{{{i},{arena},{capacity},{ceiling},[{",".join(map(command,ops))}]}}')
    p=folder/'entry.bend'
    chunks=[rows[i:i+32] for i in range(0,len(rows),32)]
    text='import Base\nimport ./conformance.bend as C\nimport ./store.bend as S\nimport ./protocol.bend as P\n'
    for i,chunk in enumerate(chunks):
        text+=f'\ndef batch_{i}() -> IO(Unit):\n  C.run(['+',\n    '.join(chunk)+'])\n'
    text+='\ndef main() -> IO(Unit):\n  do IO<Unit>:\n'
    text+=''.join(f'    batch_{i}()\n' for i in range(len(chunks)))
    p.write_text(text)
    return p

MUTANTS = [
 ('reuse-generation','Free{U32.add(generation,1)}','Free{generation}'),
 ('accept-padding','put_bound(U32.is_lt(index,capacity)','put_bound(U32.is_le(index,capacity)'),
 ('replace-occupied-owner','Denied{Live{generation,previous},Occupied{},value}','Denied{Live{generation,value},Occupied{},previous}'),
 ('forget-arena','take_arena(U32.is_eq(arena,realm)','take_arena(True{}'),
 ('ceiling-stays-reusable','vacant(U32.is_lt(generation,ceiling)','vacant(U32.is_le(generation,ceiling)'),
 ('reverse-free-order','Con{index,free},free)','List.append(&2,U32,free,[index]),free)'),
]

def compare(output, cases):
    rows=output.splitlines()
    require(len(rows)==len(cases), ('missing-observations',len(rows),len(cases)))
    failures=[]
    for i,(row,case) in enumerate(zip(rows,cases)):
        fields=row.split('|')
        require(len(fields)==3 and fields[0]==str(i), ('bad-row',i,row[:300]))
        actual,model=fields[1:]
        if actual!=model or (case[5] is not None and (actual!=case[5] or model!=case[5])):
            failures.append(dict(index=i,case=case[0],actual=actual,model=model,literal=case[5]))
    return failures

def main():
    BUILD.mkdir(parents=True,exist_ok=True); RECEIPTS.mkdir(exist_ok=True)
    record=dict(date=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='incomplete',commands=[],mutants=[])
    def checked(argv):
        r=run(argv); record['commands'].append(r); require(r['exit']==0,r); return r
    try:
        cases=inputs()
        manifest=json.dumps(cases,separators=(',',':')).encode()
        with gzip.open(RECEIPTS/'inputs.json.gz','wb') as f: f.write(manifest)
        record['input_sha256']=hashlib.sha256(manifest).hexdigest()
        record['case_count']=len(cases); record['literal_witnesses']=15
        record['sources']={str(p.relative_to(ROOT)):digest(p) for p in HERE.glob('*.bend')}
        record['harness_sha256']=digest(Path(__file__))
        baseline=BUILD/'baseline'; baseline.mkdir(exist_ok=True)
        for p in HERE.glob('*.bend'): shutil.copy2(p,baseline/p.name)
        source=entry(baseline,cases)
        record['entry_sha256']=digest(source)
        checked([SEED,HERE/'PROOF.bend','--check-only'])
        checked([SEED,source,'--check-only'])
        for backend in ('native','bun'):
            output=baseline/('program.js' if backend=='bun' else 'program')
            checked([SEED,source,'-o',output])
            result=checked((['bun',output] if backend=='bun' else [output]))
            failures=compare(result['stdout'],cases)
            require(not failures,failures[:2])
            with gzip.open(RECEIPTS/f'{backend}.txt.gz','wt') as f: f.write(result['stdout'])
            result['stdout_sha256']=hashlib.sha256(result.pop('stdout').encode()).hexdigest()
            result['stdout_file']=f'{backend}.txt.gz'; result['artifact_sha256']=digest(output)
            bounds=baseline/('bounds.js' if backend=='bun' else 'bounds')
            checked([SEED,HERE/'bounds.bend','-o',bounds])
            observed=checked(['bun',bounds] if backend=='bun' else [bounds])
            require(observed['stdout']=='[take:7]/41;1;4294967295;[0];[free:4294967295]\n[take:7]/41;1;4294967295;[];[retired]\n',observed)
        for name,body,negative in [
          ('copied-locator','def use(+key: S.Locator) -> S.Locator & S.Locator:\n  (key,key)\n',False),
          ('store-transfer','def use(store: S.Store<O.Payload>) -> S.Store<O.Payload>:\n  store\n',False),
          ('payload-transfer','def use(value: O.Payload) -> O.Payload:\n  value\n',False),
          ('duplicate-store','def use(store: S.Store<O.Payload>) -> S.Store<O.Payload> & S.Store<O.Payload>:\n  (store,store)\n',True),
          ('duplicate-payload','def use(value: O.Payload) -> O.Payload & O.Payload:\n  (value,value)\n',True),
        ]:
            fixture=baseline/f'{name}.bend'; fixture.write_text('import Base\nimport ./store.bend as S\nimport ./observe.bend as O\n'+body)
            result=run([SEED,fixture,'--check-only']); record['commands'].append(result)
            require(result['exit']!=0 and 'consumed more than once' in result['stderr'] if negative else result['exit']==0,result)
        # A mutant must still type-check and run. Only changed observations count as kills.
        for name,old,new in MUTANTS:
            folder=BUILD/name; folder.mkdir(exist_ok=True)
            for p in HERE.glob('*.bend'): shutil.copy2(p,folder/p.name)
            p=folder/'store.bend'; text=p.read_text(); require(text.count(old)==1,('mutation-anchor',name)); p.write_text(text.replace(old,new))
            source=entry(folder,cases[:15])
            checked([SEED,source,'--check-only']); checked([SEED,source,'-o',folder/'program.js'])
            result=checked(['bun',folder/'program.js']); failures=compare(result['stdout'],cases[:15])
            require(failures,('surviving-mutant',name))
            record['mutants'].append(dict(name=name,store_sha256=digest(p),status='semantic-kill',failures=failures))
        record['status']='pass'
    except Exception as error:
        record['failure']=repr(error); raise
    finally:
        (RECEIPTS/'gate.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ('status','case_count','literal_witnesses')}))

if __name__=='__main__': main()
