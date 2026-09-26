#!/usr/bin/env python3
"""Drive explicit npm file checks; retain only the wrapper's sanitized receipts."""
import hashlib,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=ROOT/'packages/symbols'
OUT=PKG/'receipts/perch-audit-2026-09-26'; OUT.mkdir(exist_ok=True)
BEND=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack']
LAW=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','symbols-bidirectional-preservation']
files=sorted(PKG.glob('*.bend'))+[PKG/'tests/remote_consumer.bend']
targets=[(p,BEND) for p in files]+[(PKG/'LAW_REVIEW.md',LAW)]+[(PKG/f'tests/perch/{n}.md',[LAW[-1]]) for n in ['clean','broken','held_out']]
summary=[]
for p,rules in targets:
 rel=str(p.relative_to(ROOT)); before=set((ROOT/'.perch/usage').glob('*.json'));start=time.monotonic()
 proc=subprocess.run(['npm','run','lint','--',rel,'--rules',','.join(rules),'--json'],cwd=ROOT,text=True,capture_output=True,timeout=180)
 matching=[]
 for f in set((ROOT/'.perch/usage').glob('*.json'))-before:
  row=json.loads(f.read_text())
  if row.get('target') in [rel,str(p)]: matching.append((f,row))
 assert len(matching)==1,{'target':rel,'exit':proc.returncode,'receipts':len(matching)}
 f,row=matching[0]; dest=OUT/(p.name.replace('.','_')+'-'+row['id']+'.json');dest.write_bytes(f.read_bytes())
 # Root receipt intentionally excludes provider errors and credentials.
 record={'target':rel,'receipt':str(dest.relative_to(PKG)),'root_receipt':str(f.relative_to(ROOT)),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'elapsed_seconds':round(time.monotonic()-start,3),'exit':proc.returncode,'status':row['status'],'checked':row['checked'],'responses':row['provider_responses'],'model':row['resolved_model'],'findings':row['findings']}
 summary.append(record);(OUT/'index.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(record),flush=True)
 if row['status'] not in ['completed','findings']: raise SystemExit('Provider or coverage failure; inspect sanitized receipt before retrying.')
 assert row['checked']==len(rules) and row['provider_responses']>0
