#!/usr/bin/env python3
"""Bounded declaration audit, preserving named CLI result + wrapper provenance."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'packages/term_store';OUT=P/'evidence/perch-parsed-review'
SOURCE='packages/term_store/main.bend'
NAMES=['Scopes.claim','Store.new','Store.alloc','Store.get','Store.set','Store.length','Store.limit','Store.snapshot','Cell.step','Cell.result','Memo.new','Memo.alloc','Memo.inspect','Memo.apply','Memo.result','memo_commit']
RULES=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack','perf-growing-prefix-copy','perf-loop-invariant-work','perf-linked-list-indexing','perf-amortized-growth']
LAWS=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','term-store-memo-completion-boundary']
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
def usage():
 rows=[]
 for path in (ROOT/'.perch/usage').glob('*.json'):
  r=json.loads(path.read_text())
  if r.get('target') in [SOURCE,'packages/term_store/LAW_REVIEW.md']:rows.append((path,r))
 return rows

def verify(receipt,rules):
 assert receipt['exit'] in [0,3] and receipt['status'] in ['completed','findings'],receipt['status']
 assert receipt['checked']==len(rules)>0
 assert receipt['provider_requests']==receipt['provider_responses']==1
 assert receipt['source_sha256']==sha(ROOT/receipt['target'])
 assert sorted(a['rule'] for a in receipt['answers'])==sorted(rules)

def check(name):
 target=SOURCE+'::'+name if name else 'packages/term_store/LAW_REVIEW.md';rules=RULES if name else LAWS
 old={r['id'] for p,r in usage()}
 args=['npm','run','lint','--',target,'--rules',','.join(rules),'--json']
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=120)
 if p.returncode not in [0,3]:raise RuntimeError(f'{target}: check failed, inspect wrapper receipt; no success recorded')
 # npm prints a heading before the one JSON object. Keep only structured output.
 result=json.loads(p.stdout[p.stdout.index('{'):])
 matches=[(p,r) for p,r in usage() if r['id'] not in old and r['selected_rules']==rules]
 assert len(matches)==1,target
 path,r=matches[0];verify(r,rules)
 assert result['checked']==len(rules)
 if name:
  assert result['name']==name and result['parser']['status']=='parsed'
  assert result['context']['basis']=='working-tree' and not result['context']['truncated']
 row={'command':args,'selected_target':target,'root_receipt':str(path.relative_to(ROOT)),'receipt':r,'cli_result':result}
 dest=OUT/((name.replace('.','-') if name else 'LAW_REVIEW')+'.json');dest.write_text(json.dumps(row,indent=2)+'\n')
 print(json.dumps({'target':target,'checked':r['checked'],'model':r['resolved_model'],'findings':r['findings']}),flush=True)
 return row

OUT.mkdir(exist_ok=True)
rows=[]
for name in NAMES:
 if name=='Scopes.claim' and '--reuse-observed-pilot' in sys.argv:
  path=ROOT/'.perch/usage/2026-09-26T22-14-29.026Z-94f6132c-615c-4744-939e-798cfe3ac11e.json';r=json.loads(path.read_text());verify(r,RULES)
  row={'command':['npm','run','lint','--',SOURCE+'::'+name,'--rules',','.join(RULES),'--json'],'selected_target':SOURCE+'::'+name,'root_receipt':str(path.relative_to(ROOT)),'receipt':r,'observed_cli_target':{'path':SOURCE,'name':name,'line':176,'end_line':179,'checked':10,'parser_status':'parsed','context_truncated':False},'note':'Fresh pilot in this pass. CLI JSON was inspected in tool output; full context retained in preflight.json. Root wrapper omits single-target name/context.'}
  (OUT/'Scopes-claim.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
 else:rows.append(check(name))
rows.append(check(None))
summary={'targets':[{'target':r['selected_target'],'root_receipt':r['root_receipt'],'source_sha256':r['receipt']['source_sha256'],'checked':r['receipt']['checked'],'findings':r['receipt']['findings']} for r in rows],'requests':sum(r['receipt']['provider_requests'] for r in rows),'responses':sum(r['receipt']['provider_responses'] for r in rows),'checks':sum(r['receipt']['checked'] for r in rows),'models':sorted(set(r['receipt']['resolved_model'] for r in rows))}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'requests':summary['requests'],'responses':summary['responses'],'checks':summary['checks']}),flush=True)
