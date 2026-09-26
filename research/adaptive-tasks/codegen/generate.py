#!/usr/bin/env python3
"""Capture actual seed-generated code and validate the displayed artifacts."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PROTO=HERE.parent
BEND=ROOT/'scripts/bend-reference'


def run(args):
    p=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,text=True,timeout=60)
    assert p.returncode==0,(args,p.returncode,p.stdout,p.stderr)
    return {'argv':[str(x) for x in args],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    seed=json.loads((ROOT/'research/execution-models/reference-hashes.json').read_text())
    for path,h in seed['files'].items():
        assert digest(ROOT/'.toolchain/bend-2.0.29-574b6d3'/path)==h,path
    existing=json.loads((PROTO/'receipts/checks.json').read_text())
    for path,h in existing['hashes'].items(): assert digest(PROTO/path)==h,path
    expected=existing['js_conformance']['stdout']
    commands=[]
    for suffix in ['c','js']:
        commands.append(run([BEND,PROTO/'conformance.bend','-o',HERE/('conformance.'+suffix)]))
    native_source=(HERE/'conformance.c').read_text()
    assert '#define BANGS   0' in native_source,'CPU-only build flags require BANGS=0'
    js=run(['node',HERE/'conformance.js']); assert js['stdout']==expected
    with tempfile.TemporaryDirectory(prefix='knot-codegen-view-') as folder:
        binary=Path(folder)/'conformance'
        commands.append(run(['clang','-std=c11','-O3',HERE/'conformance.c','-lpthread','-lm','-o',binary]))
        native=run([binary]); assert native['stdout']==expected
    (HERE/'conformance.stdout').write_text(expected)
    packed=run(['node',HERE/'capture-gpu.mjs'])
    (HERE/'cpu_frames.records.json').write_text(packed['stdout'])
    record=json.loads(packed['stdout'])
    assert record['fixture']==next(x for x in existing['fixtures'] if x['name']=='cpu_frames')
    inputs=['slot.bend','task.bend','conformance.bend','fixtures.bend','oracle.bend','gpu/check.mjs','gpu/tasks.wgsl']
    outputs=['conformance.c','conformance.js','conformance.stdout','cpu_frames.records.json','capture-gpu.mjs','generate.py']
    report={'date':datetime.now(timezone.utc).isoformat(),
      'scope':'Actual upstream-generated CPU code and verbatim GPU-packer capture; no Knot emitter',
      'seed':seed,'inputs':{p:digest(PROTO/p) for p in inputs},
      'outputs':{p:digest(HERE/p) for p in outputs},'commands':commands,
      'tools':{'node':run(['node','--version'])['stdout'].strip(),'bun':run(['bun','--version'])['stdout'].strip(),
        'clang':run(['clang','--version'])['stdout'].splitlines()[0]},
      'js_execution':js,'native_execution':native,'gpu_record_capture':packed,
      'gpu_execution':'not repeated; existing device receipt covers unchanged fixture/packer/shader',
      'gpu_receipt_sha256':digest(PROTO/'receipts/gpu.json'),'status':'pass'}
    (HERE/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: emitted C and JavaScript both reproduce the 11-line protocol transcript; captured the existing GPU packer for cpu_frames.')


if __name__=='__main__': main()
