#!/usr/bin/env python3
"""Targeted package audit through the root recording wrapper; no credential reads."""
import hashlib,json,pathlib,subprocess,time
P=pathlib.Path(__file__).resolve().parents[1]
ROOT=P.parents[1]
OUT=P/'evidence/perch-live'
OUT.mkdir(exist_ok=True)
BEND=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack']
LAW=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','output-builder-linear-assembly']
def receipts(target):
 result=[]
 for p in (ROOT/'.perch/usage').glob('*.json'):
  j=json.loads(p.read_text())
  if j.get('target')==target:result.append((p,j))
 return result

def run(target,rules,slug,reuse=False):
 known=receipts(target)
 if reuse:
  p,j=max(known,key=lambda x:x[1]['at'])
 else:
  before={j['id'] for _,j in known}
  for attempt in range(2):
   proc=subprocess.run(['npm','run','lint','--',target,'--rules',','.join(rules),'--json'],cwd=ROOT,capture_output=True,text=True,timeout=150)
   (OUT/f'{slug}.{attempt}.stdout').write_text(proc.stdout)
   (OUT/f'{slug}.{attempt}.stderr').write_text(proc.stderr)
   fresh=[(p,j) for p,j in receipts(target) if j['id'] not in before]
   if not fresh:raise RuntimeError(f'No wrapper receipt for {target}')
   p,j=max(fresh,key=lambda x:x[1]['at'])
   if j['provider_responses']>0 or not any(s in proc.stderr.lower() for s in ['429','rate limit','too many requests']) or attempt==1:break
   before.add(j['id']);time.sleep(15)
 digest=hashlib.sha256((ROOT/target).read_bytes()).hexdigest()
 assert j['source_sha256']==digest,(target,'source drift')
 assert j['selected_rules']==rules,(target,'rule drift')
 copied=OUT/f'{slug}.receipt.json'
 copied.write_text(json.dumps(j,indent=2)+'\n')
 result={'target':target,'receipt':str(copied.relative_to(ROOT)),'wrapper_receipt':str(p.relative_to(ROOT)),'source_sha256':digest,'status':j['status'],'checked':j['checked'],'provider_responses':j['provider_responses'],'model':j['resolved_model'],'findings':j['findings']}
 print(json.dumps(result),flush=True)
 return result

results=[run('packages/output_builder/main.bend',BEND,'main')]
for p in sorted(P.glob('*.bend')):
 if p.name!='main.bend':results.append(run(str(p.relative_to(ROOT)),BEND,p.stem))
results.append(run('packages/output_builder/evidence/remote-consumer.bend',BEND,'remote-consumer'))
results.append(run('packages/output_builder/LAW_REVIEW.md',LAW,'law-review'))
for p in sorted((P/'tests/perch').glob('*/LAW_REVIEW.md')):
 results.append(run(str(p.relative_to(ROOT)),['output-builder-linear-assembly'],'control-'+p.parent.name))
(OUT/'index.json').write_text(json.dumps(results,indent=2)+'\n')
