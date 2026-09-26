#!/usr/bin/env python3
"""Release only against a reviewed, remotely verified Vec hash. No friendly-name login."""
import hashlib,json,os,pathlib,re,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=ROOT/'packages/symbols'; BEND=ROOT/'scripts/bend-reference'
if len(sys.argv)!=2 or not re.fullmatch(r'0x[0-9a-f]{32}',sys.argv[1]):
 raise SystemExit('usage: python3 packages/symbols/scripts/publish.py <verified-vec-hash>')
dep=sys.argv[1]
def verify_vec():
 vec_release=ROOT/'packages/vec/RELEASE.json'
 r=json.loads(vec_release.read_text())
 assert r['status']=='published-and-remotely-verified' and r['returned_hash']==dep and r['expected_hash']==dep
 assert r['fresh_remote_consumer']['all_fetched_file_hashes_match']
 gates=ROOT/'packages/vec/receipts/gates.json'
 assert hashlib.sha256(gates.read_bytes()).hexdigest()==r['receipts']['gates.json'],'Vec gates receipt digest is stale'
 for f in r['upload_closure']:
  assert hashlib.sha256((ROOT/'packages/vec'/f['name']).read_bytes()).hexdigest()==f['sha256'],f
 return r
vec=verify_vec()
main=PKG/'main.bend'; s=main.read_text()
s,n=re.subn(r'import (?:\.\./vec/main\.bend|0x[0-9a-f]{32}/main\.bend) as V',f'import {dep}/main.bend as V',s)
assert n==1,'unexpected dependency import'
main.write_text(s)
records=[]
def run(args,env=None,expected=None):
 r=subprocess.run([str(a) for a in args],cwd=ROOT,text=True,capture_output=True,env=env,timeout=600)
 record={'command':[str(a) for a in args],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 records.append(record)
 (PKG/'receipts/release-commands.json').write_text(json.dumps(records,indent=2)+'\n')
 if r.returncode: raise RuntimeError(record)
 if expected is not None: assert r.stdout.strip()==expected,record
 return r.stdout
run(['python3',PKG/'scripts/gates.py'])
run(['python3',PKG/'scripts/benchmark.py'])
closure=json.loads((PKG/'receipts/closure.json').read_text())
assert closure['closure_ready'],'exact closure is not ready for publication'
# Every upload file is an owned reviewed file. Dependency is a published hash.
for f in closure['files']:
 assert hashlib.sha256((PKG/f['path']).read_bytes()).hexdigest()==f['sha256']
vec=verify_vec()  # Recheck the repaired gate digest immediately before publication.
response=run([BEND,PKG/'release.bend','--publish'])
found=re.findall(r'^0x[0-9a-f]{32}$',response,re.M)
assert found==[closure['expected_hash']],{'expected':closure['expected_hash'],'returned':found}
hub_hash=found[0]
fresh=pathlib.Path(tempfile.mkdtemp(prefix='fresh-',dir=PKG/'build'))
cache=fresh/'lib'; assert not cache.exists()
env=dict(os.environ,BEND_LIB=str(cache))
consumer=fresh/'consumer.bend'
consumer.write_text((PKG/'example.bend').read_text().replace('import ./main.bend as S',f'import {hub_hash}/main.bend as S\nimport {hub_hash}/release.bend as Verified'))
run([BEND,consumer,'--check-only'],env,expected='All terms check.')
for lane in ['js','native']:
 binary=fresh/f'consumer{".js" if lane=="js" else ""}'
 run([BEND,consumer,'-o',binary],env)
 run(['bun',binary] if lane=='js' else [binary],env,expected='1')
for f in closure['files']:
 remote=cache/hub_hash/f['path']
 assert remote.exists() and hashlib.sha256(remote.read_bytes()).hexdigest()==f['sha256'],f
for f in vec['upload_closure']:
 remote=cache/dep/f['name']
 assert remote.exists() and hashlib.sha256(remote.read_bytes()).hexdigest()==f['sha256'],f
receipt={'status':'published-and-remotely-verified','compiler':closure['compiler'],'revision':closure['revision'],'expected_hash':closure['expected_hash'],'returned_hash':hub_hash,'import':f'import {hub_hash}/main.bend as S','release_import':f'import {hub_hash}/release.bend as Verified','dependency':{'vec':dep,'release_receipt_sha256':hashlib.sha256((ROOT/'packages/vec/RELEASE.json').read_bytes()).hexdigest(),'verified_gates_sha256':vec['receipts']['gates.json'],'fresh_dependency_files_verified':len(vec['upload_closure'])},'license':'MIT-0','closure':closure['files'],'gates':'receipts/gates.json','benchmark':'receipts/benchmark.json','mutations':'receipts/mutations.json','fresh_cache':str(cache),'fresh_consumer':str(consumer),'fresh_lanes':{'native':'1','js':'1'},'remote_closure_sha256_verified':True,'gpu':'unvalidated','perch':'offline coverage verified; live calibration unavailable','proof_boundary':'three universal conversion laws; five concrete normalization laws; bounded trace refinement runtime checks'}
(PKG/'RELEASE.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
