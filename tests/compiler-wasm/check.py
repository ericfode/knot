#!/usr/bin/env python3
"""Build/drive Bend, invoke real Wasm, and compare literal observations."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
TIMEOUT_SCALE = float(__import__('os').environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only; gates set it under load

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
HOST_CHECKS = json.loads((ROOT / 'tests/compiler-modules/host-check-expectations.json').read_text())['entries']
BUILD=ROOT/'.local/compiler-wasm/gate'
GENERATED=HERE/'generated'
SEED=ROOT/'scripts/bend-reference'
RECEIPT=HERE/'receipts/wasm.json'
HOST=ROOT/'scripts/run-wasm.mjs'

def require(condition,detail):
    if not condition: raise AssertionError(detail)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(argv,timeout=45*TIMEOUT_SCALE):
    try:
        p=subprocess.run([str(x) for x in argv],cwd=ROOT,text=True,capture_output=True,timeout=timeout)
        return {'argv':[str(x) for x in argv],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv':[str(x) for x in argv],'exit':None,'outcome':'Exhausted','budget_seconds':timeout,'stdout':'','stderr':''}
def successful(argv):
    r=run(argv);require(r['exit']==0,r);return r
def diagnostic(r,status,prefix):
    require(r['exit']==status and prefix in r['stderr'] and r['stdout']=='',r)
def value(r,case,call):
    expected=f"Evaluated\t{case['type_id']}\t{call['tag']}\t{case['constructors'][call['tag']]}{{}}"
    require(r['exit']==0 and r['stdout'].strip()==expected,(expected,r))
def build(command,path,out,extra=()):
    out.unlink(missing_ok=True)
    r=successful([*command,path,out,*extra]);require(r['stdout'].strip()==f'Built\t{out.stat().st_size}',r)
    require(out.read_bytes()[:8]==bytes([0,97,115,109,1,0,0,0]),r)
    require(section_ids(out.read_bytes())==[1,3,7,10],r)
    return r

def section_ids(data):
    at=8;ids=[]
    while at<len(data):
        ids.append(data[at]);at+=1;length=0
        for shift in range(0,35,7):
            byte=data[at];at+=1;length|=(byte&127)<<shift
            if byte<128:break
        else:raise AssertionError('oversized section length')
        require(length<=4294967295 and at+length<=len(data),'section boundary')
        at+=length
    require(at==len(data),'section exhaustion')
    return ids

def mvp_instructions(wat):
    allowed={'local.get','local.set','i32.const','i32.eq','call','if','else','end'}
    observed=set()
    for line in wat.splitlines():
        line=line.strip()
        if not line or line==')' or line.startswith(('(module','(type','(func','(export','(local',';;')):continue
        op=line.split()[0].rstrip(')')
        require(op in allowed,('instruction outside declared profile',line));observed.add(op)
    return sorted(observed)

MUTANTS=[
 ('zero-constants','wasm.bend','W.positive_signed(cap,tag)','W.positive_signed(cap,0)','flag','main',[],1,'wasm'),
 ('inverted-branch','wasm.bend','W.bytes(cap,[70,4,127])','W.bytes(cap,[71,4,127])','flag','flip',[0],1,'wasm'),
 ('alias-parameters','wasm.bend','parameters(tail,U32.add(level,1),U32.add(index,1),Con{Local{level,index},locals})','parameters(tail,U32.add(level,1),U32.add(index,1),Con{Local{level,0},locals})','argument-order','second',[0,1],1,'wasm'),
 ('wrong-local-store','wasm.bend','instruction(cap,33,index)','instruction(cap,33,0)','shadowing','main',[],1,'wasm'),
 ('unsigned-signed-leb','wasm-bytes.bend','Bool.pick(U32,signed,64,128)','128','high-tags','signed_edge',[],64,'domain'),
 ('zero-oracle-values','eval.bend','Done{Return{Value{type_id,tag},frames}}','Done{Return{Value{type_id,0},frames}}','flag','main',[],1,'eval'),
 ('evaluate-erased-initializer','eval.bend','U32.is_eq(q,0),u => Done{Evaluate{body,env,frames}}','False{},u => Done{Evaluate{body,env,frames}}','erased-cost','main',[],1,'fuel'),
]

def main():
    BUILD.mkdir(parents=True,exist_ok=True);GENERATED.mkdir(exist_ok=True)
    manifest=json.loads((HERE/'cases.json').read_text());old=json.loads((ROOT/'tests/compiler-checker/cases.json').read_text())
    record={'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'incomplete','profile':'knot-enum-1','seed_revision':'574b6d39a235b539eb19a5c532993a0abb3d11ad'}
    try:
        paths=[*sorted((ROOT/'src').glob('*.bend')),ROOT/'src/SPEC.md',ROOT/'src/CONTRACT.json',HOST,HERE/'cases.json',HERE/'make-manifest.py',Path(__file__),*[ROOT/c['file'] for c in manifest['cases']],*[ROOT/c['file'] for c in old['cases'] if c['knot']['exit']!=0]]
        record['inputs']={str(p.relative_to(ROOT)):digest(p) for p in paths}
        record['tools']={t:successful([t,'--version'])['stdout'].strip() for t in ('bun','node','python3','wasm2wat')}
        require(record['tools']['node']=='v22.22.3',record['tools'])
        require(os.uname().sysname=='Darwin' and os.uname().machine=='arm64',os.uname())
        record['host']={'os':os.uname().sysname,'machine':os.uname().machine,'release':os.uname().release}
        record['proof']=successful([SEED,ROOT/'src/runtime-PROOF.bend']);require(record['proof']['stdout'].strip()=='All terms check.',record['proof'])
        record['builds']=[];lanes={}
        for lane in ('native','bun'):
            prefix=[] if lane=='native' else ['bun'];suffix='' if lane=='native' else '.js'
            compiler=BUILD/('compile-cli'+suffix);evaluator=BUILD/('eval-cli'+suffix)
            for source,out in [('compile-cli.bend',compiler),('eval-cli.bend',evaluator)]:
                r=successful([SEED,ROOT/'src'/source,'-o',out]);record['builds'].append({'build':r,'sha256':digest(out)})
            lanes[lane]={'compiler':[*prefix,compiler],'evaluator':[*prefix,evaluator]}
        record['fixtures']=[];modules={};case_by_name={Path(c['file']).stem:c for c in manifest['cases']}
        for case in manifest['cases']:
            name=Path(case['file']).stem;path=ROOT/case['file'];item={'file':case['file'],'lanes':{},'reference':[]}
            for i,call in enumerate(case['calls']):
                wrapper=BUILD/(name+'-reference-'+str(i)+'.bend')
                imported=os.path.relpath(path,wrapper.parent)
                wrapper.write_text(f'import {imported} as F\n\ndef main() -> F.{case["type"]}:\n  {call["seed"]}\n')
                reference=successful([SEED,wrapper]);expected=imported.removesuffix('.bend')+'.'+case['constructors'][call['tag']]+'{}'
                require(reference['stdout'].strip()==expected,(expected,reference));item['reference'].append({'source':wrapper.read_text(),'result':reference})
            for lane,commands in lanes.items():
                out=BUILD/(name+'-'+lane+'.wasm');compiled=build(commands['compiler'],path,out)
                observations=[]
                for call in case['calls']:
                    evaluated=run([*commands['evaluator'],path,call['export'],65536,*call['arguments']]);value(evaluated,case,call)
                    wasm=successful(['node',HOST,out,call['export'],*call['arguments']]);answer=json.loads(wasm['stdout'])
                    require(answer['validated'] is True and answer['result']==call['tag'],(call,wasm))
                    observations.append({'call':call,'evaluator':evaluated,'wasm':wasm})
                item['lanes'][lane]={'compile':compiled,'sha256':digest(out),'observations':observations}
                if lane=='native':
                    modules[name]=out;shutil.copy2(out,GENERATED/(name+'.wasm'))
                    disassembly=successful(['wasm2wat',out]);(GENERATED/(name+'.wat')).write_text(disassembly['stdout'])
                    item['sections']=section_ids(out.read_bytes());item['instructions']=mvp_instructions(disassembly['stdout'])
                else:require(out.read_bytes()==modules[name].read_bytes(),(name,'native/Bun bytes differ'))
            record['fixtures'].append(item)
        record['rejects']=[]
        for case in old['cases']:
            expected=case['knot']
            if expected['exit']==0:continue
            for lane,commands in lanes.items():
                out=BUILD/('reject-'+lane+'.wasm');out.unlink(missing_ok=True)
                r=run([*commands['compiler'],ROOT/case['file'],out]);diagnostic(r,expected['exit'],expected['diagnostic']);require(not out.exists(),r)
                ev=run([*commands['evaluator'],ROOT/case['file'],'main',65536]);diagnostic(ev,expected['exit'],expected['diagnostic'])
                record['rejects'].append({'file':case['file'],'lane':lane,'compiler':r,'evaluator':ev,'artifact_created':False})
        record['boundaries']=[];flag=ROOT/case_by_name['flag']['file']
        for lane,commands in lanes.items():
            boundaries=[('characters', [0,512,512,4096,65536],'lex'),('parser',[65536,0,512,4096,65536],'parse'),('checker',[65536,512,0,4096,65536],'check'),('emitter',[65536,512,512,0,65536],'emit'),('output-short',[65536,512,512,4096,67],'emit')]
            for label,args,phase in boundaries:
                out=BUILD/f'boundary-{lane}.wasm';out.unlink(missing_ok=True)
                r=run([*commands['compiler'],flag,out,*args]);diagnostic(r,4,'Exhausted\t'+phase+'\t');require(not out.exists(),r)
                record['boundaries'].append({'name':label,'lane':lane,'result':r,'artifact_created':False})
            out=BUILD/f'exact-{lane}.wasm';r=build(commands['compiler'],flag,out,[65536,512,512,4096,68]);require(out.read_bytes()==modules['flag'].read_bytes(),r)
            record['boundaries'].append({'name':'exact-output-budget','lane':lane,'result':r,'sha256':digest(out)})
            for fixture,budget,ok in [('flag',0,False),('flag',7,False),('flag',8,True),('erased-cost',5,False),('erased-cost',6,True)]:
                c=case_by_name[fixture];r=run([*commands['evaluator'],ROOT/c['file'],'main',budget])
                if ok:value(r,c,c['calls'][0])
                else:diagnostic(r,4,'Exhausted\teval\t')
                record['boundaries'].append({'name':fixture+'-transitions-'+str(budget),'lane':lane,'result':r})
            # Recognized unsupported frontend syntax still produces no module.
            for label,source in [('import','import Base\n'),('literal','def main() -> U32:\n  7\n'),('fields','type T is Type:\n  T{x: T}\n')]:
                p=BUILD/(label+'.bend');p.write_text(source);out=BUILD/f'unsupported-{lane}.wasm';out.unlink(missing_ok=True)
                r=run([*commands['compiler'],p,out]);diagnostic(r,3,'Unsupported\t');require(not out.exists(),r)
                record['boundaries'].append({'name':label,'lane':lane,'source':source,'result':r,'artifact_created':False})
            # A stale file is not an emitted artifact after rejection.
            stale=BUILD/f'stale-{lane}.wasm';stale.write_bytes(b'stale-output')
            invalid=next(c for c in old['cases'] if Path(c['file']).stem=='affine-reuse')
            r=run([*commands['compiler'],ROOT/invalid['file'],stale]);diagnostic(r,2,'Invalid\tcheck\taffine-reuse\t');require(stale.read_bytes()==b'stale-output',r)
            record['boundaries'].append({'name':'stale-output-preserved-with-failure','lane':lane,'result':r})
            for label,argv in [('missing-source', [*commands['compiler'],BUILD/'missing.bend',BUILD/'never.wasm']),('directory-output', [*commands['compiler'],flag,BUILD]),('bad-budget',[*commands['compiler'],flag,BUILD/'never.wasm',65536,512,512,4096,'bad']),('huge-budget',[*commands['compiler'],flag,BUILD/'never.wasm',65536,512,512,4096,4294967295]),('argument-range',[*commands['evaluator'],flag,'flip',100,4294967295]),('argument-arity',[*commands['evaluator'],flag,'flip',100]),('missing-export',[*commands['evaluator'],flag,'absent',100])]:
                r=run(argv);diagnostic(r,5,'HostFailure\t');record['boundaries'].append({'name':label,'lane':lane,'result':r})
        record['mutants']=[]
        for name,file,old_text,new_text,witness,export,args,expected,kind in MUTANTS:
            directory=BUILD/name;directory.mkdir(exist_ok=True)
            for source in (ROOT/'src').glob('*.bend'):shutil.copy2(source,directory/source.name)
            target=directory/file;text=target.read_text();require(text.count(old_text)==1,(name,'unique mutation'));target.write_text(text.replace(old_text,new_text))
            entry='eval-cli.bend' if kind in ('eval','fuel') else 'compile-cli.bend'
            typecheck=successful([SEED,directory/entry,'--check-only']);require(typecheck['stdout'].strip()==HOST_CHECKS[entry]['stdout'].strip(),typecheck)
            program=directory/'cli.js';compiled=successful([SEED,directory/entry,'-o',program]);c=case_by_name[witness]
            item={'name':name,'file':file,'old':old_text,'new':new_text,'source_sha256':digest(target),'typecheck':typecheck,'build':compiled,'witness':c['file'],'export':export,'arguments':args,'expected_tag':expected}
            if kind in ('eval','fuel'):
                r=run(['bun',program,ROOT/c['file'],export,6 if kind=='fuel' else 65536,*args])
                if kind=='fuel':diagnostic(r,4,'Exhausted\teval\t')
                else:require(r['exit']==0 and int(r['stdout'].split('\t')[2])!=expected,r)
                item['actual']=r
            else:
                module=directory/'mutant.wasm';item['emission']=build(['bun',program],ROOT/c['file'],module)
                # This independent decoder must accept every mutant binary.
                item['validation']=successful(['wasm2wat',module])
                r=run(['node',HOST,module,export,*args]);item['actual']=r
                if kind=='domain':diagnostic(r,5,'result outside enum-profile bounds')
                else:require(r['exit']==0 and json.loads(r['stdout'])['result']!=expected,r)
            item['outcome']='semantic-kill';record['mutants'].append(item)
        record['generated']={str(p.relative_to(ROOT)):digest(p) for p in sorted(GENERATED.iterdir()) if p.is_file()}
        record['status']='passed'
    except Exception as e:
        record['failure']=repr(e);raise
    finally:RECEIPT.write_text(json.dumps(record,indent=2)+'\n')
    print(f"Wasm gate passed: {len(record['fixtures'])} source programs, {sum(len(c['calls']) for c in manifest['cases'])} independent reference calls in two lanes, {len(record['rejects'])} rejection pairs, {len(record['boundaries'])} boundary observations, {len(record['mutants'])} semantic mutants. {RECEIPT}")

if __name__=='__main__':main()
