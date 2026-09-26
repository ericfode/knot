#!/usr/bin/env python3
"""Targeted live audit through the root npm wrapper; never read credentials.
Copies only the wrapper's structured, credential-free receipts into package evidence.
"""
from pathlib import Path
import datetime,hashlib,json,subprocess,time,sys
ROOT=Path(__file__).resolve().parents[3]; P=ROOT/'packages/term_store'
OUT=P/'evidence/perch-audit-2026-09-26'; OUT.mkdir(exist_ok=True)
SIX=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack']
LAWS=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity']
OWN='term-store-memo-completion-boundary'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def records(target):
 out=[]
 for f in (ROOT/'.perch/usage').glob('*.json'):
  try:r=json.loads(f.read_text())
  except (OSError,json.JSONDecodeError):continue
  if r.get('target')==target:out.append((f,r))
 return out
def save(tag,path,rules,receipt,original,phase):
 assert receipt['checked']==len(rules),(tag,'missing checks',receipt)
 assert receipt['provider_requests']>0 and receipt['provider_responses']>0,(tag,'no provider coverage')
 assert receipt['source_sha256']==sha(ROOT/path),(tag,'source changed')
 assert sorted(a['rule'] for a in receipt['answers'])==sorted(rules),(tag,'incomplete responses')
 row={'phase':phase,'target':path,'source_sha256':sha(ROOT/path),'command':['npm','run','lint','--',path,'--rules',','.join(rules),'--json'],'root_receipt':str(original.relative_to(ROOT)),'receipt':receipt}
 dest=OUT/(tag+'.json');dest.write_text(json.dumps(row,indent=2)+'\n')
 print(json.dumps({'target':path,'phase':phase,'checked':receipt['checked'],'responses':receipt['provider_responses'],'model':receipt['resolved_model'],'findings':receipt['findings'],'max_probability_broken':max(1-a['probability_true'] for a in receipt['answers'])}),flush=True)
 return row

def check(tag,path,rules,phase='source',reuse=None):
 if reuse:
  f=ROOT/reuse;r=json.loads(f.read_text());return save(tag,path,rules,r,f,phase)
 for attempt in range(2):
  before={r['id'] for f,r in records(path)}
  p=subprocess.run(['npm','run','lint','--',path,'--rules',','.join(rules),'--json'],cwd=ROOT,text=True,capture_output=True,timeout=120)
  matches=[(f,r) for f,r in records(path) if r['id'] not in before and r['selected_rules']==rules]
  assert len(matches)==1,(path,'wrapper receipt unavailable')
  f,r=matches[0]
  if r['exit'] in [0,3] and r['status'] in ['completed','findings']:
   return save(tag,path,rules,r,f,phase)
  # Failed receipts remain useful but are never passes. Only rate limits retry.
  (OUT/(tag+f'-failed-{attempt}.json')).write_text(json.dumps({'phase':phase,'root_receipt':str(f.relative_to(ROOT)),'receipt':r},indent=2)+'\n')
  if attempt==0 and any(s in (p.stderr+p.stdout).lower() for s in ['429','rate limit','too many requests']):
   time.sleep(20);continue
  raise RuntimeError(f'{path}: provider/check error (receipt {f.name}); not a pass')

if __name__=='__main__':
 rows=[]
 for path in sorted(P.glob('*.bend'))+[P/'tests/remote_consumer.bend']:
  rel=str(path.relative_to(ROOT));tag='source-'+path.stem
  reuse='.perch/usage/2026-09-26T20-35-08.139Z-3a0b48ae-c82e-4a8d-90f7-baf6c2c0863c.json' if path.name=='main.bend' and '--reuse-pilot' in sys.argv else None
  rows.append(check(tag,rel,SIX,reuse=reuse))
 rows.append(check('law-review','packages/term_store/LAW_REVIEW.md',LAWS+[OWN],'law-packet'))
 for name in ['clean','broken','held_out_clean','held_out_broken']:
  rows.append(check('control-'+name,f'packages/term_store/review/{name}/LAW_REVIEW.md',[OWN],'control'))
 manifest={'scope':'TermStore audit requested by user through coordinator','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':[{'target':r['target'],'source_sha256':r['source_sha256'],'receipt_id':r['receipt']['id'],'root_receipt':r['root_receipt'],'checked':r['receipt']['checked'],'phase':r['phase']} for r in rows],'exclusions':{'tests/remote_proofs.bend':'single hash import only; local PROOF and release source reviewed','tests/negative/*.bend':'three intentional checker-failure fixtures; deterministic phase diagnostics retained in gates.json','.build/**':'ignored generated binaries, emitted C/JS, dependency caches and ten deliberate semantic mutants; originals audited','scripts/*':'host-only orchestration, not Bend semantics; six Bend rules do not apply'}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
