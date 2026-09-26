#!/usr/bin/env python3
"""Run file-scoped checks through the root receipt wrapper, without reading keys."""
import datetime,hashlib,json,pathlib,subprocess,time
P=pathlib.Path(__file__).resolve().parents[1];ROOT=P.parents[1]
OUT=P/('receipts/perch-audit-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ'));OUT.mkdir(exist_ok=False)
bend=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack']
laws=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','package-int-map-union-observation']
package=['package-int-map-union-observation']
targets=[(p,bend) for p in sorted(P.glob('*.bend'))]+[(P/'receipts/remote-consumer.bend',bend),(P/'LAW_REVIEW.md',laws)]+[(P/f'tests/perch/{name}/LAW_REVIEW.md',package) for name in ['clean','broken','held_out','held_out_equal_values']]
index=[]
def receipts(target):
 out=[]
 for p in (ROOT/'.perch/usage').glob('*.json'):
  r=json.loads(p.read_text())
  if r.get('target')==target:out.append((p,r))
 return sorted(out,key=lambda x:x[1]['at'])
for p,rules in targets:
 target=str(p.relative_to(ROOT)); digest=hashlib.sha256(p.read_bytes()).hexdigest()
 # Every new audit gets fresh provider observations.
 reuse=[]
 attempts=[]
 if reuse:
  got=reuse[0]
 else:
  for attempt in range(2):
   prior={r['id'] for _,r in receipts(target)}
   run=subprocess.run(['npm','run','lint','--',target,'--rules',','.join(rules),'--json'],cwd=ROOT,text=True,capture_output=True)
   newer=[x for x in receipts(target) if x[1]['id'] not in prior]
   assert len(newer)==1,(target,'missing or ambiguous wrapper receipt')
   got=newer[0];attempts.append(got)
   if got[1]['status'] in ['completed','findings']:break
   rate_limited=any(s in run.stderr.lower() for s in ['rate limit','rate_limit','429','too many requests'])
   if not rate_limited or attempt:break
   print('Rate-limited; one retry after 15s: '+target,flush=True);time.sleep(15)
 row=got[1]
 assert row['source_sha256']==digest
 for src,r in attempts or [got]:(OUT/(r['id']+'.json')).write_text(json.dumps(r,indent=2)+'\n')
 item=dict(target=target,source_sha256=digest,root_receipt=str(got[0].relative_to(ROOT)),receipt=str((OUT/(row['id']+'.json')).relative_to(P)),id=row['id'],checked=row['checked'],status=row['status'],model=row['resolved_model'],responses=row['provider_responses'],findings=row['findings'],attempt_ids=[r['id'] for _,r in attempts or [got]])
 index.append(item);(OUT/'index.json').write_text(json.dumps(index,indent=2)+'\n')
 print(json.dumps({k:item[k] for k in ['target','checked','status','model','responses','findings']}),flush=True)
 if row['status'] not in ['completed','findings']:
  if 'missing-key'==row['status']:raise SystemExit('Credential failure; stopped, not a pass.')
print('AUDIT TARGETS RECORDED',flush=True)
