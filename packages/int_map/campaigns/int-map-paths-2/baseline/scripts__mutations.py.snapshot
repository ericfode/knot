#!/usr/bin/env python3
"""Orchestrates Bend fixtures; does not implement map semantics."""
import hashlib, json, pathlib, shutil, subprocess
P=pathlib.Path(__file__).resolve().parents[1]
ROOT=P.parents[1]
BEND=ROOT/'scripts/bend-reference'
mutants=[
 ('discard_set','Entry{key,v}\n    case Con{False{},tail}:','Tip{}\n    case Con{False{},tail}:','boundary/absence/overwrite/removal/persistence'),
 ('lose_sibling','Branch{set_path(V,tail,low(V,m),key,v),high(V,m)}','Branch{set_path(V,tail,low(V,m),key,v),Tip{}}','boundary/absence/overwrite/removal/persistence'),
 ('truncate_high_bit','bits(32n,key)','bits(31n,key)','all-32-bits/complements'),
 ('stale_remove','remove_path(V,bits(32n,key),m)','m','boundary/absence/overwrite/removal/persistence'),
 ('false_contains','case Some{x}: True{}','case Some{x}: False{}','boundary/absence/overwrite/removal/persistence'),
 ('bad_size','case Entry{k,v}: 1n','case Entry{k,v}: 0n','boundary/absence/overwrite/removal/persistence'),
 ('discard_fold','case Entry{k,v}: step(acc,k,v)','case Entry{k,v}: acc','fold-exact-contents/order'),
 ('reverse_fold','IntMap.fold(~V,~A,~step,hi,IntMap.fold(~V,~A,~step,lo,acc))','IntMap.fold(~V,~A,~step,lo,IntMap.fold(~V,~A,~step,hi,acc))','fold-exact-contents/order'),
 ('reverse_combiner','case Some{left}: combine(left,right)','case Some{left}: combine(right,left)','noncommutative/add/max/union-identities'),
 ('combine_singleton','case None{}: right','case None{}: combine(right,right)','noncommutative/add/max/union-identities'),
 ('double_combine','case Some{left}: combine(left,right)','case Some{left}: combine(combine(left,right),right)','noncommutative/add/max/union-identities'),
]
results=[]
for name,old,new,expected in mutants:
 d=P/'build/mutants'/name;d.mkdir(parents=True,exist_ok=True)
 for p in P.glob('*.bend'):shutil.copy2(p,d/p.name)
 source=(d/'main.bend').read_text()
 assert old in source,name
 source=source.replace(old,new)
 if name in ('combine_singleton','double_combine'): source=source.replace('right: V','+right: V')
 (d/'main.bend').write_text(source)
 fixture={'truncate_high_bit':'F.bit_cases(32n,1)','reverse_fold':'F.order_case()','discard_fold':'F.order_case()','reverse_combiner':'F.unions()','combine_singleton':'F.unions()','double_combine':'F.unions()'}.get(name,'F.boundary()')
 (d/'mutation_test.bend').write_text('import Base\nimport ./fixtures.bend as F\ndef check(b: Bool) -> IO(Unit):\n  match b:\n    case False{}: IO.die(Unit,1,"'+expected+'")\n    case True{}: IO.print("SURVIVED")\ndef main() -> IO(Unit): check('+fixture+')\n')
 check=subprocess.run([str(BEND),str(d/'mutation_test.bend'),'--check-only'],text=True,capture_output=True)
 (d/'typecheck.log').write_text(check.stdout+check.stderr)
 assert check.returncode==0,(name,'not a semantic mutant',check.stderr)
 build=subprocess.run([str(BEND),str(d/'mutation_test.bend'),'-o',str(d/'test.js')],text=True,capture_output=True)
 assert build.returncode==0,(name,'build failure',build.stderr)
 run=subprocess.run(['bun',str(d/'test.js')],text=True,capture_output=True)
 (d/'result.log').write_text(run.stdout+run.stderr)
 # The failure message, without PASS, identifies the unchanged assertion.
 failed=[line for line in (run.stdout+run.stderr).splitlines() if not line.startswith('PASS ')]
 killed=run.returncode!=0 and any(expected in line for line in failed)
 row=dict(name=name,baseline_sha256=hashlib.sha256((P/"main.bend").read_bytes()).hexdigest(),mutant_sha256=hashlib.sha256((d/"main.bend").read_bytes()).hexdigest(),unchanged_fixture_sha256=hashlib.sha256((d/"fixtures.bend").read_bytes()).hexdigest(),typecheck='pass',runtime_exit=run.returncode,expected=expected,killed=killed,output=run.stdout+run.stderr)
 results.append(row)
 print(json.dumps(row),flush=True)
 assert killed,(name,'survived or wrong failure')
(P/'build/mutations.json').write_text(json.dumps(results,indent=2)+'\n')
