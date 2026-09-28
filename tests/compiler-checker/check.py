#!/usr/bin/env python3
"""Drive Bend implementation and fixed observations; no compiler semantics."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
TIMEOUT_SCALE = float(__import__('os').environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only; gates set it under load

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BUILD=ROOT/'.local/compiler-checker/gate'
RECEIPT=HERE/'receipts/checker.json'
SEED=ROOT/'scripts/bend-reference'

def require(condition, detail):
    if not condition: raise AssertionError(detail)

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def run(argv, timeout=45*TIMEOUT_SCALE):
    try:
        p=subprocess.run([str(x) for x in argv],cwd=ROOT,text=True,capture_output=True,timeout=timeout)
        return {'argv':[str(x) for x in argv],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv':[str(x) for x in argv],'exit':None,'outcome':'Exhausted','budget_seconds':timeout,'stdout':'','stderr':''}

def successful(argv):
    r=run(argv);require(r['exit']==0,r);return r

def observe(r, expected):
    require(r['exit']==expected['exit'],r)
    if 'stdout' in expected: require(r['stdout'].strip()==expected['stdout'],r)
    if 'diagnostic' in expected: require(expected['diagnostic'] in r['stderr'],r)
    if expected['exit'] in (2,3,4): require(r['stdout']=='',r)

MUTANTS=[
 ('accept-affine-reuse','scope.bend','contains(ys,h),u => C.invalid','False{},u => C.invalid','affine-reuse'),
 ('accept-erased-live','scope.bend','Bool.and(live,U32.is_eq(q,0)),u =>','False{},u =>','erased-type-live'),
 ('lose-refinement','scope.bend','Scope{refine(bindings,level,tag),next','Scope{bindings,next','matched-duplicate'),
 ('lose-shadow-identity','scope.bend','C.Binding{token,next,q,type_id,False{}','C.Binding{token,0,q,type_id,False{}','shadowing'),
 ('accept-missing-arm','check.bend','Nat.is_eq(List.length(&2,C.Constructor,tokens),List.length(&2,U32,seen))','True{}','missing-arm'),
 ('accept-wrong-reference-type','check.bend','U32.is_eq(type_id,actual),u => Done{value}','True{},u => Done{value}','shadowing-type'),
 ('execute-erased-arguments','scope.bend','Bool.and(live,U32.is_ne(q,0))','live','erased-forward'),
]

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    record={'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'incomplete',
            'scope':'Resolved syntax and semantic checking; no evaluator or Wasm emitter',
            'seed_revision':'574b6d39a235b539eb19a5c532993a0abb3d11ad'}
    try:
        manifest=json.loads((HERE/'cases.json').read_text())
        paths=sorted((ROOT/'src').glob('*.bend'))+[ROOT/'src/SPEC.md',HERE/'cases.json',HERE/'make-manifest.py',HERE/'bounds.bend',Path(__file__)]+[ROOT/c['file'] for c in manifest['cases']]
        record['inputs']={str(p.relative_to(ROOT)):digest(p) for p in paths}
        record['tools']={t:successful([t,'--version'])['stdout'].strip() for t in ('bun','node','python3')}
        record['seed_inputs']={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'.toolchain/bend-2.0.29-574b6d3/bend2').glob('*.ts'))}
        record['proof']=successful([SEED,ROOT/'src/check-PROOF.bend'])
        require(record['proof']['stdout'].strip()=='All terms check.',record['proof'])
        js=BUILD/'check-cli.js';native=BUILD/'check-cli'
        record['builds']=[successful([SEED,ROOT/'src/check-cli.bend','-o',p]) for p in (js,native)]
        record['generated']={str(p.relative_to(ROOT)):digest(p) for p in (js,native)}
        lanes={'bun':['bun',js],'native':[native]}
        record['fixtures']=[]
        require({str(p.relative_to(ROOT)) for p in (HERE/'fixtures').glob('*.bend')}=={c['file'] for c in manifest['cases'] if c['file'].startswith('tests/compiler-checker/fixtures/')},'Fixture manifest mismatch')
        for case in manifest['cases']:
            ref=run([SEED,ROOT/case['file']]);observe(ref,case['reference'])
            item={'file':case['file'],'reference':ref,'lanes':{}}
            for name,command in lanes.items():
                actual=run([*command,ROOT/case['file']]);observe(actual,case['knot']);item['lanes'][name]=actual
            record['fixtures'].append(item)
        record['budgets']=[]
        flag=next(c for c in manifest['cases'] if Path(c['file']).stem=='flag')
        for name,command in lanes.items():
            for depth in (0,1,3,4,5):
                r=run([*command,ROOT/flag['file'],65536,depth])
                observe(r,flag['knot'] if depth>=4 else {'exit':4,'diagnostic':'Exhausted\tcheck\tbudget\t'})
                record['budgets'].append({'lane':name,'depth':depth,'result':r})
        record['bounds']=[]
        bounds_expected=('Done 256\nExhausted\tcheck\tbudget\t0:0:1:0\n'*4).strip()
        for suffix,command in (('.js',['bun']),('',[])):
            output=BUILD/('bounds'+suffix)
            build=successful([SEED,HERE/'bounds.bend','-o',output])
            r=successful([*command,output]);require(r['stdout'].strip()==bounds_expected,r)
            record['bounds'].append({'build':build,'observation':r,'sha256':digest(output)})
        record['mutants']=[]
        for name,file,old,new,witness in MUTANTS:
            directory=BUILD/name
            directory.mkdir(exist_ok=True)
            for source in (ROOT/'src').glob('*.bend'): shutil.copy2(source,directory/source.name)
            target=directory/file;source=target.read_text();require(source.count(old)==1,(name,'mutation must be unique'))
            target.write_text(source.replace(old,new))
            typecheck=successful([SEED,directory/'check-cli.bend','--check-only'])
            require(typecheck['stdout'].strip()=='All terms check.',typecheck)
            out=directory/'check-cli.js';build=successful([SEED,directory/'check-cli.bend','-o',out])
            case=next(c for c in manifest['cases'] if Path(c['file']).stem==witness)
            actual=run(['bun',out,ROOT/case['file']]);require(actual['exit'] in (0,2,3),actual)
            try: observe(actual,case['knot'])
            except AssertionError: killed=True
            else: killed=False
            require(killed,(name,'survived'))
            record['mutants'].append({'name':name,'file':file,'old':old,'new':new,'source_sha256':digest(target),'typecheck':typecheck,'build':build,'witness':case['file'],'expected':case['knot'],'actual':actual,'outcome':'semantic-kill'})
        record['status']='passed'
    except Exception as e:
        record['failure']=repr(e)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record,indent=2)+'\n')
    print(f"Checker gate passed: {len(record['fixtures'])} reference fixtures, {2*len(record['fixtures'])} checked observations, 10 depth and 16 catalog-bound observations, {len(record['mutants'])} semantic mutants; {RECEIPT}")

if __name__=='__main__': main()
