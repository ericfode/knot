#!/usr/bin/env python3
"""Run each planned Perch review once, retaining its exact invocation and output."""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess, time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('review',choices=['style','slot-1','slot-2','laws'])
args=parser.parse_args()
receipts=HERE/'receipts'
out=receipts/('perch-'+args.review+'-command.json')
assert not out.exists(),'Preserve the first review; no automatic retry'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pre=json.loads((HERE/'preregistration.json').read_text())
for path,digest in pre['frozen_files'].items(): assert sha(ROOT/path)==digest,path
lock=json.loads((HERE/'submission-lock.json').read_text())
for row in lock['submissions']:
    assert sha(ROOT/row['source'])==row['source_sha256']
    assert sha(ROOT/row['blind_path'])==row['source_sha256']
if args.review=='style':
    context=json.loads((receipts/'style-preflight.json').read_text())['cohort']
    argv=['npm','run','lint:style','--','--live',
        '.local/life-review/slot-1/life.bend','.local/life-review/slot-2/life.bend',
        '--cohort='+context,'--jobs=2','--output=research/life-blueberry/receipts/style.json']
elif args.review=='laws':
    rules='law-domain-inhabited,law-observable-essence,law-public-contract-coverage,law-independent-model,law-state-composition,law-boundaries-and-exhaustion,law-mutation-sensitivity,law-proof-claim-integrity'
    argv=['npm','run','lint','--','research/life-blueberry/LAW_REVIEW.md','--rules',rules]
else:
    rules='bend-machine-arithmetic,bend-fuel-completeness,perf-growing-prefix-copy,perf-linked-list-indexing'
    argv=['npm','run','lint','--','.local/life-review/'+args.review+'/life.bend','--rules',rules]
start=time.monotonic()
result=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,timeout=120)
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,
    'exit':result.returncode,'seconds':time.monotonic()-start,
    'stdout':result.stdout,'stderr':result.stderr,'review':args.review}
out.write_text(json.dumps(record,indent=2)+'\n')
if args.review!='style' and '{' in result.stdout:
    try:
        parsed=json.JSONDecoder().raw_decode(result.stdout[result.stdout.index('{'):])[0]
        (receipts/('perch-'+args.review+'.json')).write_text(json.dumps(parsed,indent=2)+'\n')
    except json.JSONDecodeError:
        pass
print(json.dumps({'review':args.review,'exit':result.returncode,'seconds':record['seconds'],'receipt':str(out)}))
raise SystemExit(result.returncode)
