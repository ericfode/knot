#!/usr/bin/env python3
"""Build Bend emitters/oracles, move their bytes, invoke Wasm and compare receipts."""
from pathlib import Path
import datetime, gzip, hashlib, json, shutil, subprocess, time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BUILD=ROOT/'.local/flat-store'
RECEIPTS=HERE/'receipts'
SEED=ROOT/'scripts/bend-reference'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(test, detail):
    if not test: raise AssertionError(str(detail)[:1600])
def run(argv,timeout=90):
    start=time.monotonic()
    try:
        p=subprocess.run(list(map(str,argv)),cwd=ROOT,text=True,capture_output=True,timeout=timeout)
        return dict(argv=list(map(str,argv)),exit=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed_seconds=time.monotonic()-start)
    except subprocess.TimeoutExpired:
        return dict(argv=list(map(str,argv)),exit=None,status='harness-timeout',elapsed_seconds=time.monotonic()-start)

def command(op):
    if op[0]=='put':return f'P.Insert{{{op[1]},{op[2]}}}'
    if op[0]=='alloc':return f'P.Reserve{{{op[1]}}}'
    tag={'take':'Extract','drop':'Dispose'}[op[0]]
    return f'P.{tag}{{S.Locator{{{op[1]},{op[2]},{op[3]}}}}}'

def oracle_entry():
    cases=json.load(gzip.open(ROOT/'research/owned-store/receipts/inputs.json.gz','rt'))
    rows=[]
    for i,(_,arena,capacity,ceiling,ops,_) in enumerate(cases):
        rows.append(f'P.Case{{{i},{arena},{capacity},{ceiling},[{",".join(map(command,ops))}]}}')
    s='import Base\nimport ../../research/flat-store/oracle.bend as O\nimport ../../research/owned-store/store.bend as S\nimport ../../research/owned-store/protocol.bend as P\n'
    groups=[rows[i:i+32] for i in range(0,len(rows),32)]
    for i,group in enumerate(groups):s+=f'\ndef batch_{i}() -> IO(Unit):\n  O.tests(['+',\n    '.join(group)+'])\n'
    s+='\ndef main() -> IO(Unit):\n  do IO<Unit>:\n'+''.join(f'    batch_{i}()\n' for i in range(len(groups)))
    s+=f'    O.boundary({len(cases)},4294967294)\n    O.boundary({len(cases)+1},4294967295)\n'
    p=BUILD/'oracle-entry.bend';p.write_text(s);return p

MUTANTS=[
 ('reuse-generation','runtime.bend','A.write_field(3,4,[A.get(5),A.word(1),A.op(106)])','A.write_field(3,4,[A.get(5)])'),
 ('accept-padding','runtime.bend','A.guard(A.concat([[A.get(0)],A.header(4),[A.op(79)]]),A.failure(3,[A.get(1)]))','A.guard(A.concat([[A.get(0)],A.header(4),[A.op(75)]]),A.failure(3,[A.get(1)]))'),
 ('overwrite-on-rejection','runtime.bend','A.failure(7,[A.get(1)])','A.concat([A.write_field(2,8,[A.get(1)]),A.failure(7,[A.get(1)])])'),
 ('ignore-arena','runtime.bend','A.guard(A.concat([[A.get(0)],A.header(0),[A.op(71)]]),A.failure(4,[A.word(0)]))','A.guard([A.word(0)],A.failure(4,[A.word(0)]))'),
 ('wrap-at-ceiling','runtime.bend','[A.get(5)], A.header(8), [A.op(73)','[A.get(5)], A.header(8), [A.op(77)'),
 ('lose-free-tail','runtime.bend','A.write_field(3,12,A.header(12))','A.write_field(3,12,[A.none()])'),
 ('erase-allocated-payload','runtime.bend','A.write_field(2,8,[A.get(1)])','A.write_field(2,8,[A.word(0)])'),
 ('zero-sentinel','assembly.bend','W.bytes(cap,[65,127])','W.bytes(cap,[65,0])'),
 ('write-on-reinit','runtime.bend','A.guard([A.global_get()],[A.word(10),A.op(15)])','A.guard([A.global_get()],A.concat([A.write_header(0,[A.get(0)]),[A.word(10),A.op(15)]]))'),
]

def main():
    BUILD.mkdir(parents=True,exist_ok=True);RECEIPTS.mkdir(exist_ok=True)
    record=dict(status='incomplete',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),commands=[],mutants=[])
    def checked(argv):
        r=run(argv);record['commands'].append(r);require(r['exit']==0,r);return r
    def move_bytes(result,path):
        data=json.loads(result['stdout']);require(all(isinstance(x,int) and 0<=x<=255 for x in data),'not bytes')
        Path(path).write_bytes(bytes(data));result['stdout_sha256']=hashlib.sha256(result.pop('stdout').encode()).hexdigest()
    try:
        entry=oracle_entry()
        record['sources']={str(p.relative_to(ROOT)):digest(p) for folder in [HERE,ROOT/'research/owned-store'] for p in folder.glob('*.bend')}
        record['harnesses']={str(p.relative_to(ROOT)):digest(p) for p in [HERE/'check.py',HERE/'run-wasm.mjs']}
        record['oracle_entry_sha256']=digest(entry)
        record['original_inputs_sha256']=digest(ROOT/'research/owned-store/receipts/inputs.json.gz')
        record['literal_probes_sha256']=digest(HERE/'probes.json')
        checked([SEED,HERE/'PROOF.bend','--check-only'])
        checked([SEED,HERE/'emit-cli.bend','--check-only']);checked([SEED,entry,'--check-only'])
        for backend in ('native','bun'):
            emitter=BUILD/('emitter.js' if backend=='bun' else 'emitter')
            oracle=BUILD/('oracle.js' if backend=='bun' else 'oracle')
            checked([SEED,HERE/'emit-cli.bend','-o',emitter]);checked([SEED,entry,'-o',oracle])
            probe=BUILD/('probes.js' if backend=='bun' else 'probes')
            checked([SEED,HERE/'probes.bend','-o',probe])
            observed=checked(['bun',probe] if backend=='bun' else [probe])
            require(observed['stdout'].splitlines()==json.loads((HERE/'probes.json').read_text()),('literal probes',backend,observed))
            module=BUILD/f'{backend}.wasm'
            emitted=checked(['bun',emitter] if backend=='bun' else [emitter]);move_bytes(emitted,module)
            expected=checked(['bun',oracle] if backend=='bun' else [oracle])
            (BUILD/f'{backend}-oracle.txt').write_text(expected['stdout'])
            with gzip.open(RECEIPTS/f'{backend}-oracle.txt.gz','wt') as f:f.write(expected['stdout'])
            expected['stdout_sha256']=hashlib.sha256(expected.pop('stdout').encode()).hexdigest()
            expected['stdout_file']=f'{backend}-oracle.txt.gz'
            checked(['node',HERE/'run-wasm.mjs',module,BUILD/f'{backend}-oracle.txt',RECEIPTS/f'{backend}-wasm.json'])
        require((BUILD/'native.wasm').read_bytes()==(BUILD/'bun.wasm').read_bytes(),'emitter byte drift')
        require((BUILD/'native-oracle.txt').read_bytes()==(BUILD/'bun-oracle.txt').read_bytes(),'oracle backend drift')
        record['module_sha256']=digest(BUILD/'native.wasm');record['module_bytes']=(BUILD/'native.wasm').stat().st_size
        checked(['/opt/homebrew/bin/wasm2wat',BUILD/'native.wasm','-o',BUILD/'store.wat'])
        for artifact in ('native.wasm','store.wat'):shutil.copy2(BUILD/artifact,RECEIPTS/artifact)
        for name,file,old,new in MUTANTS:
            home=BUILD/'mutants'/name;source=home/'research/flat-store';source.mkdir(parents=True,exist_ok=True)
            for p in HERE.glob('*.bend'):shutil.copy2(p,source/p.name)
            if not (home/'src').exists():(home/'src').symlink_to(ROOT/'src',target_is_directory=True)
            if not (home/'research/owned-store').exists():(home/'research/owned-store').symlink_to(ROOT/'research/owned-store',target_is_directory=True)
            p=source/file;s=p.read_text();require(s.count(old)==1,('mutation anchor',name));p.write_text(s.replace(old,new))
            checked([SEED,source/'emit-cli.bend','--check-only']);checked([SEED,source/'emit-cli.bend','-o',home/'emitter.js'])
            output=checked(['bun',home/'emitter.js']);move_bytes(output,home/'store.wasm')
            result=run(['node',HERE/'run-wasm.mjs',home/'store.wasm',BUILD/'native-oracle.txt',RECEIPTS/f'mutant-{name}.json'])
            record['commands'].append(result);r=json.loads((RECEIPTS/f'mutant-{name}.json').read_text())
            require(result['exit']==3 and r['status']=='semantic-mismatch' and r['imports']==[] and len(r['exports'])==6,('not a semantic kill',name,r))
            record['mutants'].append(dict(name=name,status='semantic-kill',source_sha256=digest(p),module_sha256=digest(home/'store.wasm'),receipt=f'mutant-{name}.json'))
        record['status']='pass'
    except Exception as error:
        record['failure']=repr(error);raise
    finally:
        (RECEIPTS/'gate.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['status','module_bytes','module_sha256']}))

if __name__=='__main__':main()
