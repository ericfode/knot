#!/usr/bin/env python3
"""Publish only the reviewed pinned closure, then verify it from an empty cache."""
import datetime, hashlib, json, os, pathlib, platform, subprocess, tempfile, time
P=pathlib.Path(__file__).resolve().parents[1]
ROOT=P.parents[1]
BEND=ROOT/'scripts/bend-reference'
R=P/'receipts'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,env=None,timeout=90):
    t=time.monotonic()
    p=subprocess.run(list(map(str,args)),cwd=ROOT,env=env,text=True,capture_output=True,timeout=timeout)
    return dict(command=list(map(str,args)),exit=p.returncode,stdout=p.stdout,stderr=p.stderr,seconds=time.monotonic()-t)
def save(name,data): (R/name).write_text(json.dumps(data,indent=2)+'\n')
def success(r):
    if r['exit']!=0: raise RuntimeError(json.dumps(r,indent=2))
    return r

success(run(['bun',P/'scripts/closure.ts']))
c=json.loads((R/'closure.json').read_text());g=json.loads((R/'gates.json').read_text());m=json.loads((R/'mutations.json').read_text())
for name,h in g['source_sha256'].items(): assert sha(P/name)==h,('changed checked source',name)
for f in c['files']:
    if f['name'].endswith('.bend'): assert g['source_sha256'][f['name']]==f['sha256'],f
assert c['holes']==0 and len(m)==9 and all(x['classification']=='semantic kill' and x['typecheck']['exit']==0 and x['runtime']['run']['stdout'].strip()=='False{}' for x in m)
assert all(x['proof_rejection']['exit']!=0 for x in m)
assert all(g[k][b]['run']['stdout'].strip()=='True{}' for k in ['conformance','generic'] for b in ['native','js'])
assert g['proof']['exit']==0
assert g['ownership']['element_negative']['verified_diagnostic']=={'expected':'Data','observed':'Type','location':'illegal'}
assert g['ownership']['affine_negative']['verified_diagnostic']=={'expected':'v','observed':'v (consumed more than once)','location':'illegal'}
expected=c['expected_hash']
check=success(run([BEND,P/'release.bend','--check-only']))
publication=run([BEND,P/'release.bend','--publish'],timeout=180)
save('publication.json',{'expected_hash':expected,'check':check,'publish':publication})
success(publication)
returned=next((x for x in publication['stdout'].splitlines() if x.startswith('0x')),None)
assert returned==expected,(expected,returned,publication)
print('Published '+returned,flush=True)
cache=pathlib.Path(tempfile.mkdtemp(prefix='remote_cache_',dir=P/'build'))
assert not list(cache.iterdir())
consumer=cache.parent/('consumer_'+cache.name+'.bend')
consumer.write_text(f'''import Base
import {returned}/release.bend as Release
import {returned}/main.bend as V

def read(pair: V.Vec<U32> & Result<V.Error,U32>) -> Bool:
  (v,r) = pair
  match r:
    case Fail{{e}}: False{{}}
    case Done{{x}}: U32.is_eq(x,42)

def pushed(pair: V.Vec<U32> & Result<V.Error,Unit>) -> Bool:
  (v,r) = pair
  read(V.Vec.get(U32,v,0))

def main() -> Bool:
  Bool.and(Release.main(),pushed(V.Vec.push(U32,V.Vec.new(U32),42)))
''')
env=dict(os.environ,BEND_LIB=str(cache))
remote={'cache':str(cache),'cache_initially_empty':True,'consumer_source':consumer.read_text(),'consumer_sha256':sha(consumer),'check':success(run([BEND,consumer,'--check-only'],env=env)),'backends':{}}
for backend,ext in [('native',''),('js','.js')]:
    output=consumer.with_suffix(ext or '.bin')
    build=success(run([BEND,consumer,'-o',output],env=env))
    result=success(run(['bun',output] if ext else [output],env=env))
    assert result['stdout'].strip()=='True{}',result
    remote['backends'][backend]={'build':build,'run':result}
remote['fetched_files']=[]
for f in c['files']:
    actual=sha(cache/returned/f['name']); assert actual==f['sha256'],f
    remote['fetched_files'].append({'name':f['name'],'sha256':actual})
manifest=''.join(f["sha256"]+' '+f['name']+'\n' for f in remote['fetched_files'])
remote['recomputed_hash']='0x'+hashlib.sha256(manifest.encode()).hexdigest()[:32]
assert remote['recomputed_hash']==returned
save('remote.json',remote)
release={
 'package':'vec','status':'published-and-remotely-verified','released_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'expected_hash':expected,'returned_hash':returned,'import':f'import {returned}/main.bend as V',
 'proof_import':f'import {returned}/release.bend as VecRelease',
 'compiler':{'version':c['compiler'],'revision':c['revision']},'dependencies':{'packages':[],'Base':'provided by pinned compiler'},
 'license':'MIT-0','upload_closure':c['files'],'closure_bytes':c['bytes'],
 'gates':{'proof_holes':0,'element_parametric_fixed_shape_laws':19,'concrete_normalizations':6,'general_all_states_refinement_proved':False,'bounded_traces_per_backend':12288,'named_trace_families':7,'native':True,'javascript':True,'generic_record_and_string_runtime':True,'gpu':'not tested or claimed','semantic_mutants_killed':9,'mutation_law_rejections':9,'largest_scaling_n':262144,'perch':'9 relevant rules selected; complete packets; live inference unavailable without PERCH_API_KEY'},
 'fresh_remote_consumer':{'initially_empty_cache':True,'checked':True,'native_result':'True{}','javascript_result':'True{}','all_fetched_file_hashes_match':True},
 'environment':{'platform':platform.platform(),'machine':platform.machine(),'bun':success(run(['bun','--version']))['stdout'].strip(),'clang':success(run(['clang','--version']))['stdout'].strip()},
 'receipts':{x.name:sha(x) for x in sorted(R.glob('*.json'))},
 'reviewed_documents':{x:sha(P/x) for x in ['SPEC.md','LAW_REVIEW.md','INTERFACE.md']},
 'limitations':['Data elements only; vector ownership is affine','No all-length universal refinement theorem','No GPU validation','Policy limit is typed; actual host OOM is not recoverable','Private constructors/helpers are outside the public API']
}
(P/'RELEASE.json').write_text(json.dumps(release,indent=2)+'\n')
print('Fresh-cache native and JS consumers passed; all remote file hashes match.',flush=True)
