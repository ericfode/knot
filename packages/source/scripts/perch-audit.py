#!/usr/bin/env python3
"""Targeted live audit using the repository wrapper. Never reads credentials."""
import pathlib,json,subprocess,hashlib,time,datetime
ROOT=pathlib.Path(__file__).resolve().parents[3]; P=ROOT/'packages/source'; OUT=P/'receipts/perch-audit-2026-09-26';OUT.mkdir(exist_ok=True)
BEND=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack']
LAWS=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity']
RULE='source-checkpoint-observation'
files=sorted(P.glob('*.bend'))+sorted((P/'tests').glob('*.bend'))
targets=[(str(p.relative_to(ROOT)),BEND) for p in files]+[('packages/source/LAW_REVIEW.md',LAWS+[RULE])]+[(f'packages/source/tests/perch/{name}.md',[RULE]) for name in ['clean','broken','held_out','held_out_broken']]
# The first two real wrapper runs were inspected interactively; retain them once.
preexisting={'packages/source/main.bend':'3ccf0268-2540-4043-bd20-e8d2ee165462','packages/source/model.bend':'e8233c6e-3e69-4213-8f0a-f9cb29a03749'}
def find_receipt(target,after='',rid=None):
 rows=[]
 for f in (ROOT/'.perch/usage').glob('*.json'):
  r=json.loads(f.read_text())
  if r.get('target')==target and r['at']>=after and (rid is None or r['id']==rid):rows.append((r['at'],f,r))
 return sorted(rows)[-1][1:]
records=[]
for target,rules in targets:
 if target in preexisting:
  original,r=find_receipt(target,rid=preexisting[target]);attempts=[]
 else:
  attempts=[]
  for attempt in range(2):
   start=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
   command=['npm','run','lint','--',target,'--rules',','.join(rules),'--json']
   got=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
   original,r=find_receipt(target,after=start)
   attempts.append({'receipt_id':r['id'],'exit':got.returncode})
   # Do not retain arbitrary provider errors or environment. Wrapper receipts
   # contain only structured answers and safe operational metadata.
   if got.returncode in (0,3):break
   if attempt==0 and any(x in (got.stderr+got.stdout).lower() for x in ['429','rate limit','rate-limit']):time.sleep(15);continue
   break
 assert hashlib.sha256((ROOT/target).read_bytes()).hexdigest()==r['source_sha256'],'Refusing stale audit receipt'
 expected=len(rules)
 complete=r['provider_responses']>0 and r['checked']==expected and len(r['answers'])==expected and r['status'] in ['completed','findings']
 local=OUT/(r['id']+'.json');local.write_text(json.dumps(r,indent=2)+'\n')
 record={'target':target,'source_sha256':r['source_sha256'],'receipt':str(local.relative_to(ROOT)),'wrapper_receipt':str(original.relative_to(ROOT)),'checked':r['checked'],'expected':expected,'complete':complete,'status':r['status'],'model':r['resolved_model'],'attempts':attempts,'findings':r['findings'],'answers':r['answers']}
 records.append(record);print(target,r['status'],r['checked'],r['findings'],flush=True)
 (OUT/'index.json').write_text(json.dumps({'date':'2026-09-26','records':records},indent=2)+'\n')
assert all(r['complete'] for r in records),'Incomplete provider coverage; inspect index.'
