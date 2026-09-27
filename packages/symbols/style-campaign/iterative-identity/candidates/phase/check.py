from pathlib import Path
import subprocess,json,time,sys,hashlib
root=Path('/Users/ericfode/src/knot'); out=Path(sys.argv[1]).resolve(); records=[]
for name,cmd,expected in [('main',[root/'scripts/bend-reference',out/'main.bend','--check-only'],'All terms check.'),('proof',[root/'scripts/bend-reference',out/'PROOF.bend','--check-only'],'All terms check.'),('native-build',[root/'scripts/bend-reference',out/'conformance.bend','-o',out/'conformance'],None),('native-run',[out/'conformance'],'1'),('js-build',[root/'scripts/bend-reference',out/'conformance.bend','-o',out/'conformance.js'],None),('js-run',['bun',out/'conformance.js'],'1')]:
 a=time.monotonic(); r=subprocess.run([str(x) for x in cmd],cwd=root,text=True,capture_output=True,timeout=180)
 record=dict(name=name,command=[str(x) for x in cmd],exit=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.monotonic()-a)
 if expected is not None: record['expected_stdout']=expected; record['output_matches']=r.stdout.strip()==expected
 records.append(record); (out/'gates.json').write_text(json.dumps({'source_sha256':hashlib.sha256((out/'main.bend').read_bytes()).hexdigest(),'records':records},indent=2)+'\n')
 print(json.dumps(record),flush=True)
 if r.returncode!=0 or expected is not None and r.stdout.strip()!=expected: sys.exit(1)
