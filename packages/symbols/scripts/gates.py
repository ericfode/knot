#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=ROOT/'packages/symbols'; BEND=ROOT/'scripts/bend-reference'
def fingerprint():
 paths=list(PKG.glob('*.bend'))+[PKG/'LICENSE',ROOT/'packages/vec/main.bend',ROOT/'packages/vec/LICENSE']
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=fingerprint()
records=[]
def run(args,expected=None):
 r=subprocess.run([str(a) for a in args],cwd=ROOT,text=True,capture_output=True,timeout=180)
 records.append({'command':[str(a) for a in args],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 assert r.returncode==0,records[-1]
 if expected is not None: assert r.stdout.strip()==expected,records[-1]
run([BEND,PKG/'PROOF.bend','--check-only'],'All terms check.')
for entry in ['conformance','release']:
 for lane in ['js','native']:
  dest=PKG/'build'/f'{entry}{".js" if lane=="js" else ""}'
  run([BEND,PKG/f'{entry}.bend','-o',dest])
  run(['bun',dest] if lane=='js' else [dest],'1')
run(['python3',PKG/'scripts/mutations.py'])
run(['bun',PKG/'scripts/inspect.ts'])
sha={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PKG.glob('*.bend'))}
review=PKG/'LAW_REVIEW.md'; text=review.read_text().split('<!-- SOURCE_HASHES -->')[0]
review.write_text(text+'<!-- SOURCE_HASHES -->\n\nReviewed Bend source SHA-256 (refreshed by scripts/gates.py):\n\n```text\n'+''.join(f'{v}  {k}\n' for k,v in sha.items())+'```\n')
run(['node',PKG/'scripts/perch-wiring.mjs'])
assert fingerprint()==before,'source or dependency changed during gates; rerun on stable files'
(PKG/'receipts/gates.json').write_text(json.dumps({'source_sha256':sha,'checked_inputs_sha256':before,'records':records},indent=2)+'\n')
print('PASS: proof zero holes, native/JS conformance and release consumer, eight semantic mutants, closure audit, Perch offline wiring.')
