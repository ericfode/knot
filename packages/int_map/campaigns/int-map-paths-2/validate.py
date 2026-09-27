"""Candidate acceptance using unchanged gates; never overwrites release receipts."""
import hashlib,json,pathlib,shutil,subprocess,time
ROOT=pathlib.Path.cwd();P=ROOT/'packages/int_map';O=pathlib.Path(__file__).resolve().parent;BUILD=P/'build/int-map-paths-2';BUILD.mkdir(parents=True,exist_ok=True)
pre=json.loads((O/'preregistration.json').read_text());rows=[]
assert (P/'main.bend').read_bytes()==(O/'candidate-first.bend.snapshot').read_bytes(), 'Candidate gates require the exact recorded candidate source.'
assert (P/'scripts/mutations.py').read_bytes()==(O/'candidate-mutations.py.snapshot').read_bytes(), 'Candidate mutation locators required.'
def run(name,args):
 t=time.perf_counter();r=subprocess.run(list(map(str,args)),cwd=ROOT,text=True,capture_output=True,timeout=180)
 row=dict(name=name,args=list(map(str,args)),exit=r.returncode,seconds=time.perf_counter()-t,stdout=r.stdout,stderr=r.stderr);rows.append(row)
 (O/'gates.json').write_text(json.dumps({'steps':rows},indent=2)+'\n')
 assert r.returncode==0,(name,r.stdout,r.stderr)
 print(name+' PASS',flush=True)
for f,h in pre['baseline_sha256'].items():
 if f not in ('main.bend','scripts/mutations.py'):assert hashlib.sha256((P/f).read_bytes()).hexdigest()==h,('fixed input changed',f)
run('proof-zero-holes',['scripts/bend-reference',P/'PROOF.bend','--check-only'])
for backend,ext,runner in [('native','',[]),('javascript','.js',['bun'])]:
 exe=BUILD/('release'+ext)
 run(backend+'-build',['scripts/bend-reference',P/'release.bend','-o',exe]);run(backend+'-conformance',runner+[exe])
run('semantic-mutants',['python3',P/'scripts/mutations.py'])
shutil.copy2(P/'build/mutations.json',O/'mutations.json')
run('performance-model-gates',['python3',P/'scripts/performance.py'])
shutil.copy2(P/'build/performance.json',O/'performance.json')
for f,h in pre['baseline_sha256'].items():
 if f not in ('main.bend','scripts/mutations.py'):assert hashlib.sha256((P/f).read_bytes()).hexdigest()==h,('fixed input changed',f)
result={'accepted_deterministically':True,'candidate_sha256':hashlib.sha256((P/'main.bend').read_bytes()).hexdigest(),'immutable_inputs_unchanged':True,'mutation_locator_changes':True,'compiler_retry_used':False,'steps':rows}
(O/'gates.json').write_text(json.dumps(result,indent=2)+'\n');print('ALL CANDIDATE GATES PASS',flush=True)
