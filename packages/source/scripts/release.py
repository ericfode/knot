#!/usr/bin/env python3
"""Release reviewed Source closure; verify package and Vec in an empty remote cache."""
import datetime,hashlib,json,os,pathlib,platform,subprocess,tempfile,time
P=pathlib.Path(__file__).resolve().parents[1]; ROOT=P.parents[1]; R=P/'receipts'; BEND=ROOT/'scripts/bend-reference'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):(R/name).write_text(json.dumps(x,indent=2)+'\n')
def run(args,env=None):
 start=time.monotonic();r=subprocess.run(list(map(str,args)),cwd=ROOT,env=env,text=True,capture_output=True)
 return {'command':list(map(str,args)),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'seconds':time.monotonic()-start}
def ok(r):
 if r['exit_code']:raise RuntimeError(json.dumps(r))
 return r
ok(run(['bun',P/'scripts/closure.ts']))
c=json.loads((R/'closure.json').read_text());g=json.loads((R/'gates.json').read_text());m=json.loads((R/'mutations.json').read_text());sc=json.loads((R/'scaling.json').read_text())
for receipt in [g,m,sc]:
 for name,h in receipt['sources'].items():assert sha(P/name)==h,('checked source changed',name)
allowed={'LAWS.bend','LICENSE','PROOF.bend','benchmark.bend','conformance.bend','example.bend','main.bend','model.bend','observations.bend','proof_observations.bend','release.bend','tests/invalid_scalars.bend','types.bend'}
assert set(c['files'])==allowed and c['holes']==0
for name,meta in c['files'].items():assert sha(P/name)==meta['sha256']
assert len(m['mutants'])==11 and all(x['status']=='semantic-kill' and x['typecheck']['code']==0 and x['mutant']['output'].strip()=='0' for x in m['mutants'])
assert all(g[b]['code']==0 and g[b]['output'].strip()=='1' for b in ['native','js','native_invalid_scalars'])
assert g['proof']['code']==0 and all(row[b]['verified'] for row in sc['rows'] for b in ['native','js'])
dep=json.loads((ROOT/'packages/vec/RELEASE.json').read_text());assert dep['status']=='published-and-remotely-verified'
assert dep['returned_hash']=='0xd684886d10b431b9dce6c3b2d1ef1980'
expected=c['expected_hash']
check=ok(run([BEND,P/'release.bend','--check-only']))
pub=run([BEND,P/'release.bend','--publish']);save('publication.json',{'expected_hash':expected,'check':check,'publication':pub});ok(pub)
returned=next((s for s in pub['stdout'].splitlines() if s.startswith('0x')),None)
assert returned==expected,(returned,expected)
print('Published '+returned,flush=True)
consumer=P/'tests/remote_consumer.bend'
consumer.write_text(f'''import Base
import {returned}/release.bend as Release
import {returned}/conformance.bend as Checks
import {returned}/main.bend as S
import {returned}/types.bend as T

def read(r: Result<T.Error,String>) -> Bool:
  match r:
    case Fail{{e}}: False{{}}
    case Done{{x}}: String.eq(x,"😀")

def extracted(pair: S.Source & Result<T.Error,String>) -> Bool:
  (s,r) = pair
  read(r)

def built(r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{{e}}: False{{}}
    case Done{{s}}: extracted(S.Source.extract(s,T.Span{{91,1,2}}))

def main() -> Bool:
  Bool.and(Checks.all(),Bool.and(String.eq(Release.main(),"😀"),built(S.Source.new(91,"a😀\\nβ"))))
''')
cache=pathlib.Path(tempfile.mkdtemp(prefix='remote_cache_',dir=P/'build'));assert not list(cache.iterdir())
env=dict(os.environ,BEND_LIB=str(cache));remote={'initially_empty_cache':True,'cache':str(cache),'consumer_source':consumer.read_text(),'consumer_sha256':sha(consumer),'check':ok(run([BEND,consumer,'--check-only'],env)),'backends':{}}
for backend in ['native','js']:
 binary=cache.parent/('remote_consumer.js' if backend=='js' else 'remote_consumer')
 compiled=ok(run([BEND,consumer,'-o',binary],env));result=ok(run(['bun',binary] if backend=='js' else [binary],env));assert result['stdout'].strip()=='True{}',result
 remote['backends'][backend]={'compile':compiled,'run':result}
remote['files']={}
for name,meta in sorted(c['files'].items()):
 actual=sha(cache/returned/name);assert actual==meta['sha256'];remote['files'][name]=actual
manifest=''.join(h+' '+name+'\n' for name,h in remote['files'].items());remote['recomputed_hash']='0x'+hashlib.sha256(manifest.encode()).hexdigest()[:32];assert remote['recomputed_hash']==returned
remote['vec_files_verified']={}
for f in dep['upload_closure']:
 actual=sha(cache/dep['returned_hash']/f['name']);assert actual==f['sha256'];remote['vec_files_verified'][f['name']]=actual
save('remote.json',remote)
release={'package':'source','status':'published-and-remotely-verified','released_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_hash':expected,'returned_hash':returned,'import':f'import {returned}/main.bend as S','types_import':f'import {returned}/types.bend as T','proof_import':f'import {returned}/release.bend as SourceRelease','compiler':{'version':'2.0.29','revision':c['revision']},'dependencies':{'vec':dep['returned_hash'],'Base':'pinned compiler Base'},'license':'MIT-0','upload_closure':c['files'],'closure_bytes':sum(x['bytes'] for x in c['files'].values()),'gates':{'holes':0,'universal_conditional_public_laws':5,'file_id_parametric_fixed_shape_laws':5,'auxiliary_helper_laws':1,'concrete_normalizations':21,'general_all_string_refinement_proved':False,'native_cpu':True,'javascript':True,'native_malformed_char_partition':True,'semantic_mutants_killed':11,'maximum_scaling_codepoints':131072,'gpu':'not tested','perch':'9 relevant rules with complete offline request coverage; live calibration unavailable'},'fresh_remote_consumer':{'initially_empty_cache':True,'source_and_vec_file_hashes_match':True,'native':'True{}','javascript':'True{}','recomputed_hash':remote['recomputed_hash']},'environment':{'platform':platform.platform(),'machine':platform.machine(),'bun':ok(run(['bun','--version']))['stdout'].strip(),'clang':ok(run(['clang','--version']))['stdout'].strip()},'receipts':{p.name:sha(p) for p in sorted(R.glob('*.json'))},'reviewed_documents':{name:sha(P/name) for name in ['SPEC.md','INTERFACE.md','LAW_REVIEW.md']},'scripts':{p.name:sha(p) for p in sorted((P/'scripts').glob('*')) if p.is_file()},'package_rule':{'path':'.perch/rules/package_source.yaml','sha256':sha(ROOT/'.perch/rules/package_source.yaml'),'calibrated':False},'limits':['No general all-string refinement proof','No GPU execution claim','Caller owns file-ID uniqueness and immutable revision scope','Offsets are Unicode scalar values; no UTF-16 conversion','Malformed Char values are rejected by JS runtime before Source can receive them','Host allocation failure is outside typed error recovery','Source constructors/helpers are outside the supported API']}
(P/'RELEASE.json').write_text(json.dumps(release,indent=2)+'\n');print('Fresh-cache Source and Vec hashes verified; native and JS consumers passed.',flush=True)
