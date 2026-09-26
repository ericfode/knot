#!/usr/bin/env python3
"""Drive pinned Bend checks. All vector/oracle semantics remain in Bend."""
import hashlib, json, pathlib, re, shutil, subprocess, time
P = pathlib.Path(__file__).resolve().parents[1]
ROOT = P.parents[1]
BEND = ROOT / 'scripts/bend-reference'
BUILD = P/'build'
RECEIPTS = P/'receipts'
BUILD.mkdir(exist_ok=True); RECEIPTS.mkdir(exist_ok=True)

def run(args, expect=0, timeout=90):
    start=time.monotonic()
    p=subprocess.run(list(map(str,args)),cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    r=dict(command=list(map(str,args)),exit=p.returncode,stdout=p.stdout,stderr=p.stderr,seconds=time.monotonic()-start)
    if expect is not None and p.returncode != expect:
        raise RuntimeError(json.dumps(r,indent=2))
    return r

def check(file): return run([BEND,file,'--check-only'])
def build_run(file,out):
    build=run([BEND,file,'-o',out])
    execute=run(['bun',out] if str(out).endswith('.js') else [out])
    return dict(build=build,run=execute)
def save(name,data):
    (RECEIPTS/name).write_text(json.dumps(data,indent=2)+'\n')

def negative_checks():
    cases={
        'affine_negative':('v','v (consumed more than once)','affine-quantity-rejection'),
        'element_negative':('Data','Type','element-kind-rejection'),
    }
    results={}
    for name,(expected,observed,classification) in cases.items():
        fixture=P/'tests'/f'{name}.bend'
        r=run([BEND,fixture,'--check-only'],expect=None)
        diagnostic=r['stderr']+r['stdout']
        fields={k:re.search(r'^- '+k+r'\s*:\s*(.+)$',diagnostic,re.MULTILINE) for k in ['expected','observed']}
        assert r['exit']==1 and all(fields.values()),r
        assert fields['expected'].group(1)==expected and fields['observed'].group(1)==observed,r
        assert 'Location: illegal\n' in diagnostic and '- message' not in diagnostic,r
        r['verified_diagnostic']={'expected':expected,'observed':observed,'location':'illegal'}
        r['classification']=classification
        r['fixture_sha256']=hashlib.sha256(fixture.read_bytes()).hexdigest()
        results[name]=r
    return results

def ownership():
    receipt=json.loads((RECEIPTS/'gates.json').read_text())
    for name,h in receipt['source_sha256'].items():
        assert hashlib.sha256((P/name).read_bytes()).hexdigest()==h,('changed checked source',name)
    receipt['ownership']=negative_checks()
    save('gates.json',receipt)
    print('ownership negatives rejected by the intended kind/quantity diagnostics',flush=True)

def gates():
    receipt={'proof':check(P/'PROOF.bend'),'conformance':{}}
    for backend,ext in [('js','.js'),('native','')]:
        r=build_run(P/'conformance.bend',BUILD/('conformance'+ext))
        assert r['run']['stdout'].strip()=='True{}',r
        receipt['conformance'][backend]=r
    receipt['generic']={}
    for backend,ext in [('js','.js'),('native','')]:
        r=build_run(P/'generic.bend',BUILD/('generic'+ext))
        assert r['run']['stdout'].strip()=='True{}',r
        receipt['generic'][backend]=r
    receipt['ownership']=negative_checks()
    receipt['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.glob('*.bend')}
    save('gates.json',receipt)
    print('proof, native/JS conformance, ownership gates passed',flush=True)

def mutations():
    original=(P/'main.bend').read_text()
    cases=[
      ('discard_push','Array.set(Maybe<&2,T>,a,n,Some{value})','Array.set(Maybe<&2,T>,a,n,None{})','growth_values','growth_order'),
      ('drop_growth','slots = copy_slots(T,U32.to_nat(n),0,a,fresh)','slots = fresh','growth_values','growth_order'),
      ('overwrite_growth','Array.set(Maybe<&2,T>,fresh,i,x)','Array.set(Maybe<&2,T>,fresh,0,x)','growth_values','growth_order'),
      ('wrapped_get','get_if(T,n,c,d,m,a,index,U32.is_lt(index,n))','get_if(T,n,c,d,m,a,index,True{})','logical_bounds','max_index'),
      ('pop_stale_length','observed(T,last,c,d,m,Array.swap','observed(T,n,c,d,m,Array.swap','push_pop','push_pop_growth'),
      ('reverse_slice','Con{v,acc}','List.append(&1,T,acc,Con{v,Nil{}})','ranges','slice_order'),
      ('ignore_limit','U32.min(limit, Vec.maximum())','Vec.maximum()','limits','zero_limit'),
      ('reject_exact_limit','minimum,U32.is_le(minimum,m))','minimum,U32.is_lt(minimum,m))','limits','exact_limit_reserve'),
      ('failed_swap_changes_first','(Buffer{n,c,d,m,a}, Fail{Bounds{}})\n    case True{}:\n      observed(T,n,c,d,m,Array.swap','(Buffer{n,c,d,m,Array.set(Maybe<&2,T>,a,0,Some{value})}, Fail{Bounds{}})\n    case True{}:\n      observed(T,n,c,d,m,Array.swap','logical_bounds','logical_bounds'),
    ]
    results=[]
    for name,old,new,property_name,law_name in cases:
        assert original.count(old)==1,(name,original.count(old))
        d=P/'tests/generated'/name;d.mkdir(parents=True,exist_ok=True)
        for f in P.glob('*.bend'): shutil.copyfile(f,d/f.name)
        mutant=original.replace(old,new)
        if name=='pop_stale_length':
            mutant=mutant.replace('def pop_if(-T: Data, n: U32','def pop_if(-T: Data, +n: U32')
        (d/'main.bend').write_text(mutant)
        r={'name':name,'property':property_name,'intended_law':law_name,'intended_observation':property_name,'replacement':{'old':old,'new':new}}
        r['typecheck']=check(d/'main.bend')
        (d/'mutation_probe.bend').write_text(f'import Base\nimport ./conformance.bend as C\ndef main() -> Bool:\n  C.{property_name}()\n')
        r['runtime']=build_run(d/'mutation_probe.bend',d/'probe.js')
        assert r['runtime']['run']['stdout'].strip()=='False{}',r
        if law_name:
            r['proof_rejection']=run([BEND,d/'PROOF.bend','--check-only'],expect=None)
            assert r['proof_rejection']['exit']!=0,r
            # Full suite can fail at an earlier law in the same behavior family.
            assert 'expected' in r['proof_rejection']['stderr']+r['proof_rejection']['stdout'],r
            r['first_rejecting_law']=re.search(r'Location: ([^\n]+)',r['proof_rejection']['stderr']+r['proof_rejection']['stdout']).group(1)
        r['supporting_edits']=['pop_if n binder changed from affine to reusable U32 so stale-length mutant is type-correct'] if name=='pop_stale_length' else []
        r['classification']='semantic kill'
        r['mutant_sha256']=hashlib.sha256((d/'main.bend').read_bytes()).hexdigest()
        results.append(r)
        print(name+': type-correct; unchanged '+property_name+' fails',flush=True)
    save('mutations.json',results)

def scaling():
    results=[]
    for n in [4096,16384,65536,262144]:
        source=BUILD/f'bench_{n}.bend'
        source.write_text(f'import Base\nimport ../benchmark.bend as B\ndef main() -> B.Report:\n  B.workload({n}n)\n')
        out=BUILD/f'bench_{n}'
        build=run([BEND,source,'-o',out])
        samples=[run([out]) for _ in range(3)]
        expected_sum=(17*n*(n-1)//2+3*n)&0xffffffff
        expected=f'../benchmark.Report{{{n}, {n}, {n.bit_length()-1}, {n-1}, {2*n-1}, {expected_sum}, True{{}}}}'
        for r in samples: assert r['stdout'].strip()==expected,(expected,r)
        results.append({'n':n,'build':build,'runs':samples,'expected':expected,'count_source':'capacity transitions: growth copies previous length and initializes new capacity; not runtime allocator telemetry'})
        print(n,samples[0]['stdout'].strip(),flush=True)
    save('scaling.json',results)

if __name__=='__main__':
    import sys
    for name in sys.argv[1:] or ['gates','mutations','scaling']:
        {'gates':gates,'ownership':ownership,'mutations':mutations,'scaling':scaling}[name]()
