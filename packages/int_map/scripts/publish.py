#!/usr/bin/env python3
"""Publish the already-reviewed, gated closure and verify a fresh remote consumer."""
import datetime, hashlib, json, os, pathlib, re, subprocess, tempfile
P=pathlib.Path(__file__).resolve().parents[1];ROOT=P.parents[1];B=ROOT/'scripts/bend-reference'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
gates=json.loads((P/'receipts/gates.json').read_text());closure=json.loads((P/'receipts/closure.json').read_text())
assert gates['deterministic_pass'] and gates['proof_holes']==0
assert all(sha(P/k)==v for k,v in gates['source_sha256'].items()),'source changed since gates'
assert all(sha(P/f['path'])==f['sha256'] for f in closure['closure']),'closure changed since review'
assert closure['proof_holes']==0 and len(closure['closure'])==9
expected=closure['expected_hash']
record=dict(package='int_map',status='publishing',timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),compiler={'version':'2.0.29','revision':'574b6d39a235b539eb19a5c532993a0abb3d11ad','command':'scripts/bend-reference'},dependencies=['pinned Base only'],license='MIT-0',expected_hash=expected,closure=closure['closure'],closure_bytes=closure['bytes'],deterministic_gates={'pass':True,'proof_holes':0,'receipt':'receipts/gates.json','mutants_killed':len(json.loads((P/'receipts/mutations.json').read_text())),'cpu':True,'javascript':True,'gpu':False},perch={'eligible_rules':9,'completed_model_requests':0,'calibration':'unavailable: PERCH_API_KEY not set','receipt':'receipts/perch.json'},receipts=[])
def save(): (P/'RELEASE.json').write_text(json.dumps(record,indent=2)+'\n')
def command(label,args,env=None):
 r=subprocess.run(list(map(str,args)),cwd=ROOT,env=env,text=True,capture_output=True)
 record['receipts'].append(dict(label=label,args=list(map(str,args)),exit=r.returncode,stdout=r.stdout,stderr=r.stderr));save()
 if r.returncode:raise RuntimeError(label+': '+r.stdout+r.stderr)
 print(label+' PASS',flush=True);return r.stdout
try:
 save()
 output=command('publish',[B,P/'release.bend','--publish'])
 got=re.findall(r'^0x[0-9a-f]{32}$',output,re.M)
 assert got==[expected],('returned hash mismatch',got,expected)
 record.update(returned_hash=got[0],import_api=f'import {expected}/main.bend as M',import_proofs=f'import {expected}/PROOF.bend as Proof',status='published_remote_verification_pending');save()
 cache=pathlib.Path(tempfile.mkdtemp(prefix='fresh-bend-lib-',dir=P/'build'))
 assert not list(cache.iterdir());record['fresh_cache']={'path':str(cache),'initially_empty':True}
 consumer=P/'build/remote-consumer.bend'
 consumer.write_text('''import Base
import HASH/main.bend as M
import HASH/release.bend as Remote

def matches(x: Maybe<&2,U32>, expected: U32) -> Bool:
  match x:
    case None{}: False{}
    case Some{v}: U32.is_eq(v,expected)

def checked(ok: Bool) -> IO(Unit):
  match ok:
    case False{}: IO.die(Unit,1,"REMOTE consumer failed")
    case True{}: IO.print("REMOTE snapshot/union=ok")

def consumer() -> IO(Unit):
  +left = M.IntMap.set(U32,M.IntMap.empty(U32),4294967295,7)
  right = M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),4294967295,6),0,0)
  +result = M.IntMap.union_with(~U32,~(a => b => U32.add(U32.mul(a,100),b)),left,right)
  checked(Bool.and(matches(M.IntMap.get(U32,left,4294967295),7),
    Bool.and(matches(M.IntMap.get(U32,result,4294967295),706),
      Bool.and(matches(M.IntMap.get(U32,result,0),0),Nat.is_eq(M.IntMap.size(U32,result),2n)))))

def main() -> IO(Unit):
  do IO<Unit>:
    Remote.main()
    consumer()
'''.replace('HASH',expected))
 env=dict(os.environ,BEND_LIB=str(cache));record['fresh_cache']['consumer_sha256']=sha(consumer)
 expected_output=next(x['stdout'] for x in gates['steps'] if x['name']=='native_run')+'REMOTE snapshot/union=ok\n'
 for backend,suffix,runner in [('native','',[]),('javascript','.js',['bun'])]:
  target=P/'build'/('remote-consumer'+suffix)
  command('fresh_'+backend+'_build',[B,consumer,'-o',target],env)
  out=command('fresh_'+backend+'_run',runner+[target],env)
  assert out==expected_output,('remote consumer output mismatch',backend,out)
 fetched=cache/expected
 remote_files=sorted(str(p.relative_to(fetched)) for p in fetched.rglob('*') if p.is_file())
 assert remote_files==sorted(f['path'] for f in closure['closure']),remote_files
 assert all(sha(fetched/f['path'])==f['sha256'] for f in closure['closure']),'remote source differs'
 record['fresh_cache'].update(files=remote_files,all_file_hashes_match=True,native_output_matches=True,javascript_output_matches=True)
 record['status']='complete';save()
 (P/'receipts/remote-consumer.bend').write_text(consumer.read_text())
 print('RELEASE COMPLETE '+expected,flush=True)
except Exception as e:
 record['status']='blocked';record['blocker']=str(e);save();raise
