#!/usr/bin/env python3
"""Publish only a reviewed, frozen closure, then verify it from a fresh cache."""
from pathlib import Path
import subprocess,os,json,time,hashlib,datetime,platform,re
ROOT=Path(__file__).resolve().parents[3]; P=ROOT/'packages/term_store'; BEND=ROOT/'scripts/bend-reference'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
closure=json.loads((P/'evidence/closure.json').read_text()); gates=json.loads((P/'evidence/gates.json').read_text())
assert gates.get('source_sha256'), 'complete final gate receipt required'
for name,expected in gates['source_sha256'].items(): assert sha(P/name)==expected,('source changed after gates',name)
for f in closure['files']: assert sha(P/f['name'])==f['sha256'],('closure changed',f['name'])
assert {'PROOF.bend','LAWS.bend','LICENSE','main.bend','model.bend'} <= {x['name'] for x in closure['files']}
v=json.loads((ROOT/'packages/vec/RELEASE.json').read_text()); assert v['status']=='published-and-remotely-verified'
assert v['import'] in (P/'main.bend').read_text()
assert sha(ROOT/'packages/vec/receipts/gates.json')==v['receipts']['gates.json'], 'Vec receipt refresh incomplete'
expected=closure['expected_hash']
def run(name,args,env=None,timeout=600):
 start=time.monotonic();r=subprocess.run([str(a) for a in args],cwd=ROOT,env=env,text=True,capture_output=True,timeout=timeout)
 receipt={'name':name,'command':[str(a) for a in args],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'seconds':time.monotonic()-start}
 (P/'evidence'/f'{name}.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(name,r.returncode,flush=True)
 assert r.returncode==0,receipt
 return receipt
published=run('publication',[BEND,P/'release.bend','--publish'])
assert expected in published['stdout'].splitlines(),('returned hash differs',expected,published)
cache=P/'.build'/('fresh-cache-'+str(time.time_ns()));cache.mkdir(parents=True);assert not list(cache.iterdir())
env=dict(os.environ,BEND_LIB=str(cache))
consumer=(P/'example.bend').read_text().replace('import ./main.bend as S',f'import {expected}/main.bend as S\nimport {expected}/conformance.bend as C')
consumer=consumer.replace('  created(S.Store.new(U32,S.Scopes.new(),2))','  do IO<Unit>:\n    created(S.Store.new(U32,S.Scopes.new(),2))\n    C.main()')
(P/'tests/remote_consumer.bend').write_text(consumer)
(P/'tests/remote_proofs.bend').write_text(f'import {expected}/release.bend as R\n')
proof=run('remote-proof',[BEND,P/'tests/remote_proofs.bend','--check-only'],env=env)
assert 'All terms check.' in proof['stdout']
results={}
for target,suffix,prefix in [('native','',[]),('javascript','.js',['bun'])]:
 out=P/'.build'/('remote-consumer'+suffix)
 run('remote-'+target+'-compile',[BEND,P/'tests/remote_consumer.bend','-o',out],env=env)
 r=run('remote-'+target+'-run',prefix+[out],env=env)
 assert r['stdout'].startswith('term=73\n') and 'PASS 128-mixed-histories-x128-operations\n' in r['stdout']
 results[target]=r['stdout']
verified=[]
for f in closure['files']:
 local=cache/expected/f['name'];assert local.is_file() and sha(local)==f['sha256'],('remote mismatch',f)
 verified.append(f['name'])
for f in v['upload_closure']:
 local=cache/v['returned_hash']/f['name'];assert local.is_file() and sha(local)==f['sha256'],('dependency mismatch',f)
remote={'initially_empty_cache':True,'cache':str(cache),'proof_checked':True,'native':results['native'],'javascript':results['javascript'],'all_package_file_hashes_match':True,'verified_files':verified,'all_dependency_file_hashes_match':True,'consumer_source_sha256':sha(P/'tests/remote_consumer.bend')}
(P/'evidence/remote.json').write_text(json.dumps(remote,indent=2)+'\n')
release={'package':'term_store','status':'published-and-remotely-verified','released_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_hash':expected,'returned_hash':expected,'import':f'import {expected}/main.bend as S','proof_import':f'import {expected}/release.bend as TermStoreRelease','compiler':{'version':'Bend 2.0.29','revision':'574b6d39a235b539eb19a5c532993a0abb3d11ad'},'dependencies':{'vec':v['returned_hash'],'Base':'pinned compiler standard library'},'license':'MIT-0','upload_closure':closure['files'],'closure_bytes':closure['total_bytes'],'gates':{'proof_holes':0,'quantified_theorems':7,'concrete_normalizations':7,'arbitrary_store_refinement':False,'runtime_store_history_operations':16384,'native':True,'javascript':True,'generic_first_order_term_runtime':True,'semantic_mutants_killed':10,'negative_ownership_fixtures':3,'largest_scaling_n':524288,'gpu':'not tested or claimed','perch':'9 rules load and match; provider unavailable; no model verdict/calibration'},'fresh_remote_consumer':remote,'environment':{'platform':platform.platform(),'bun':subprocess.check_output(['bun','--version'],text=True).strip()},'receipts':{f.name:sha(f) for f in sorted((P/'evidence').glob('*.json'))},'reviewed_documents':{n:sha(P/n) for n in ['SPEC.md','LAW_REVIEW.md','INTERFACE.md']},'reproduction_scripts':{f.name:sha(f) for f in sorted((P/'scripts').iterdir()) if f.is_file()},'limitations':['One caller-managed Scopes chain per identity realm; independent roots may alias','Public constructor fabrication outside API contract','Serial memo protocol; no concurrent attempt tokens','Data payloads only; no affine handles','No general all-size/history store refinement theorem','No GPU validation; host OOM is a host failure'],'package_perch_rule':{'path':'.perch/rules/package_term_store.yaml','sha256':sha(ROOT/'.perch/rules/package_term_store.yaml'),'calibrated':False}}
(P/'RELEASE.json').write_text(json.dumps(release,indent=2)+'\n')
print('VERIFIED',expected,flush=True)
