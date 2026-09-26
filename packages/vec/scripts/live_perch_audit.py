#!/usr/bin/env python3
"""Record bounded live file checks through the shared npm wrapper. Never read .env."""
import concurrent.futures, datetime, hashlib, json, pathlib, subprocess, time
P=pathlib.Path(__file__).resolve().parents[1]
ROOT=P.parents[1]
OUT=P/'receipts/perch_audit_2026_09_26'
OUT.mkdir(exist_ok=True)
BEND=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack']
LAW=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','vec-logical-state-observation']

def run_one(job):
    target,rules=job
    before=set((ROOT/'.perch/usage').glob('*.json'))
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    command=['npm','run','lint','--',target,'--rules',','.join(rules),'--json']
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=180)
    paths=set((ROOT/'.perch/usage').glob('*.json'))-before
    candidates=[]
    for path in paths:
        record=json.loads(path.read_text())
        if record.get('target')==target and record.get('selected_rules')==rules:
            candidates.append((path,record))
    assert len(candidates)==1,(target,len(candidates),result.returncode)
    path,record=candidates[0]
    assert record['source_sha256']==hashlib.sha256((ROOT/target).read_bytes()).hexdigest(),target
    dest=OUT/(record['id']+'.json')
    dest.write_text(json.dumps(record,indent=2)+'\n')
    r={'target':target,'command':command,'receipt':str(dest.relative_to(ROOT)),'wrapper_receipt':str(path.relative_to(ROOT)),'started':started,'record':record}
    # Preserve the structured CLI response with rule text, not provider errors.
    idx=result.stdout.find('{')
    try:r['cli_result']=json.loads(result.stdout[idx:])
    except (ValueError,TypeError):r['cli_result']=None
    r['rate_limited']=bool('429' in result.stderr or 'rate limit' in result.stderr.lower())
    (OUT/(record['id']+'-result.json')).write_text(json.dumps({k:v for k,v in r.items() if k!='record'},indent=2)+'\n')
    print(json.dumps({'target':target,'id':record['id'],'status':record['status'],'checks':record['checked'],'responses':record['provider_responses'],'model':record['resolved_model'],'findings':record['findings']}),flush=True)
    return r

def main():
    jobs=[(str(f.relative_to(ROOT)),BEND) for f in sorted(P.glob('*.bend'))]
    jobs.append(('packages/vec/tests/remote_consumer.bend',BEND))
    jobs.append(('packages/vec/LAW_REVIEW.md',LAW))
    jobs.extend((f'packages/vec/tests/perch/{kind}/LAW_REVIEW.md',['vec-logical-state-observation']) for kind in ['clean','broken','heldout','heldout_broken'])
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for r in pool.map(run_one,jobs): records.append(r)
    retry=[]
    for r in records:
        if r['rate_limited']:
            time.sleep(10)
            retry.append(run_one((r['target'],r['record']['selected_rules'])))
    records+=retry
    (OUT/'index.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Audit requests recorded: '+str(len(records)),flush=True)
if __name__=='__main__':main()
