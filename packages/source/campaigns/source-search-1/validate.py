#!/usr/bin/env python3
"""Use the unchanged package harness in a fresh isolated validation workspace."""
import pathlib,importlib.util,shutil,json,hashlib,sys
P=pathlib.Path(__file__).resolve().parents[2];C=pathlib.Path(__file__).resolve().parent;phase=sys.argv[1]
assert phase in ['baseline','candidate']
prereg=json.loads((C/'preregistration.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in prereg['immutable_hashes'].items():assert sha(P/name)==digest,('immutable changed',name)
assert sha(C/'search_contract.bend')==prereg['supplemental_contract_sha256']
spec=importlib.util.spec_from_file_location('source_gates',P/'scripts/gates.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
W=P/'build/source-search-1'/phase/'workspace';E=C/'evidence'/phase
W.mkdir(parents=True,exist_ok=False);E.mkdir(parents=True,exist_ok=False)
for src in P.glob('*.bend'):shutil.copyfile(src,W/src.name)
(W/'tests').mkdir();shutil.copyfile(P/'tests/invalid_scalars.bend',W/'tests/invalid_scalars.bend')
g.PKG=W;g.BUILD=W/'build';g.RECEIPTS=E;g.BUILD.mkdir()
commands=[]
original_run=g.run
def record(args):
 result=original_run(args);commands.append({'command':list(map(str,args)),**result});(E/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return result
g.run=record
# New assertion body was frozen before the candidate, and also runs on baseline.
for target,runner in [('native',[]),('js',['bun'])]:
 binary=g.BUILD/('search_contract.js' if target=='js' else 'search_contract')
 g.checked([g.BEND,C/'search_contract.bend','-o',binary]);result=g.checked(runner+[binary]);assert result['output'].strip()=='1'
if phase=='candidate':
 g.gates();print('candidate proof/native/JS/invalid-scalar: PASS',flush=True)
 g.mutations();print('candidate eleven semantic mutants: PASS',flush=True)
g.scaling();print(phase+' scaling and supplemental state contract: PASS',flush=True)
(E/'identity.json').write_text(json.dumps({'source_sha256':sha(P/'main.bend'),'harness_sha256':sha(P/'scripts/gates.py'),'immutable_assertions_verified':True,'phase':phase,'script_only_redirects':'PKG to copied workspace; BUILD and RECEIPTS to fresh phase directories; original mutation locators/observers unchanged'},indent=2)+'\n')
