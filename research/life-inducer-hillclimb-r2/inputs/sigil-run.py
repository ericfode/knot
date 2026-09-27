"""Bounded fresh-context Luna experiment orchestration and receipt capture."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent


def call(ident, prompt, schema, directory, timeout=180):
    directory.mkdir(parents=True,exist_ok=True)
    receipt=directory/f'{ident}.receipt.json'
    prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
    if receipt.exists():
        prior=json.loads(receipt.read_text())
        if prior['status']=='completed' and prior['prompt_sha256']==prompt_hash:
            return {**prior,'replayed':True}
    response=directory/f'{ident}.json'
    attempt=1
    while (directory/f'{ident}.attempt-{attempt}.events.jsonl').exists(): attempt+=1
    started=time.perf_counter()
    when=datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix='phi-luna-') as cwd:
        cmd=['codex','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check',
             '--model','gpt-5.6-luna','-c','model_reasoning_effort="low"',
             '-c','project_doc_max_bytes=0','-c','approval_policy="never"',
             '--disable','apps','--disable','shell_tool','--disable','code_mode_host',
             '--disable','code_mode','--disable','code_mode_only',
             '--disable','browser_use','--disable','computer_use','--disable','remote_plugin',
             '--disable','image_generation','--enable','skip_host_skill_discovery',
             '-c','suppress_unstable_features_warning=true',
             '--sandbox','read-only','--cd',cwd,'--output-schema',str(schema),
             '--json','--output-last-message',str(response),'-']
        try:
            proc=subprocess.run(cmd,input=prompt,text=True,capture_output=True,timeout=timeout)
            output,stderr,code=proc.stdout,proc.stderr,proc.returncode
        except subprocess.TimeoutExpired as e:
            output=e.stdout or ''; stderr=e.stderr or ''; code=124
            if isinstance(output,bytes): output=output.decode(errors='replace')
            if isinstance(stderr,bytes): stderr=stderr.decode(errors='replace')
    events=[]
    for line in output.splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    usage=next((e.get('usage') for e in reversed(events) if e.get('type')=='turn.completed'),None)
    tools=[e for e in events if e.get('type') in ['item.started','item.completed']
           and e.get('item',{}).get('type') not in ['agent_message','reasoning','error']]
    status='failed'; error=None
    try:
        value=json.loads(response.read_text())
        if code==0 and usage and not tools: status='completed'
    except (OSError,ValueError) as e: error=str(e)
    (directory/f'{ident}.attempt-{attempt}.events.jsonl').write_text(output)
    (directory/f'{ident}.attempt-{attempt}.stderr.txt').write_text(stderr)
    (directory/f'{ident}.prompt.txt').write_text(prompt)
    result={'id':ident,'model':'gpt-5.6-luna','reasoning_effort':'low','status':status,
        'started_at':when,'wall_seconds_including_cli_startup':time.perf_counter()-started,
        'prompt_sha256':prompt_hash,'attempt':attempt,'exit_code':code,'usage':usage,
        'tool_events':len(tools),'error':error,'cost_usd':None,
        'warnings':[e['item'].get('message') for e in events if e.get('item',{}).get('type')=='error'],
        'cost_note':'Codex account run; per-call billed cost unavailable, not inferred.',
        'thread_id':next((e.get('thread_id') for e in events if e.get('type')=='thread.started'),None)}
    if response.exists(): result['response_sha256']=hashlib.sha256(response.read_bytes()).hexdigest()
    (directory/f'{ident}.attempt-{attempt}.receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--ids',nargs='*')
    args=parser.parse_args()
    assert 1<=args.workers<=3
    manifest=json.loads((ROOT/'manifest.json').read_text())['trials']
    if args.ids: manifest=[x for x in manifest if x['id'] in args.ids]
    start=time.perf_counter(); results=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending={pool.submit(call,m['id'],(ROOT/'prompts'/f"{m['id']}.txt").read_text(),
                    ROOT/'response.schema.json',ROOT/'responses'):m for m in manifest}
        for future in as_completed(pending):
            result=future.result(); results.append(result)
            print(json.dumps({k:result.get(k) for k in ['id','status','wall_seconds_including_cli_startup','replayed','exit_code']}),flush=True)
    report={'requested':len(manifest),'completed':sum(r['status']=='completed' for r in results),
            'wall_seconds':time.perf_counter()-start,'fresh_contexts':True,'workers':args.workers,
            'results':sorted(results,key=lambda x:x['id'])}
    (ROOT/'run.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__': main()
