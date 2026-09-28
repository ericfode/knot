#!/usr/bin/env python3
"""Capture actual seed-generated code and validate the displayed artifacts."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PROTO=HERE.parent
BEND=ROOT/'scripts/bend-reference'


def run(args):
    p=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,text=True,timeout=60,
                     env={**os.environ,'BEND_NO_TELEMETRY':'1'})
    assert p.returncode==0,(args,p.returncode,p.stdout,p.stderr)
    return {'argv':[str(x) for x in args],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    outputs=parser.add_mutually_exclusive_group()
    outputs.add_argument('--out-dir',type=Path,help='write generated artifacts here (default: .local/adaptive-tasks/codegen)')
    outputs.add_argument('--update-receipts',action='store_true',help='explicitly replace the retained generated artifacts and receipt')
    args=parser.parse_args()
    out=(args.out_dir or (HERE if args.update_receipts else ROOT/'.local/adaptive-tasks/codegen')).resolve()
    out.mkdir(parents=True,exist_ok=True)
    seed=json.loads((ROOT/'research/execution-models/reference-hashes.json').read_text())
    for path,h in seed['files'].items():
        assert digest(ROOT/'.toolchain/bend-2.0.29-574b6d3'/path)==h,path
    existing=json.loads((PROTO/'receipts/checks.json').read_text())
    assert existing['status']=='pass','historical protocol receipt did not pass'
    # Harness provenance may change without changing the model. Pin every Bend
    # input and the shader; validate the host packer's emitted records below.
    for path,h in existing['hashes'].items():
        if path.endswith('.bend') or path=='gpu/tasks.wgsl': assert digest(PROTO/path)==h,path
    expected=existing['js_conformance']['stdout']
    interpreted=run([BEND,PROTO/'conformance.bend'])
    assert interpreted['stdout']==expected,'seed protocol observations changed'
    commands=[]
    for suffix in ['c','js']:
        commands.append(run([BEND,PROTO/'conformance.bend','-o',out/('conformance.'+suffix)]))
    native_source=(out/'conformance.c').read_text()
    assert '#define BANGS   0' in native_source,'CPU-only build flags require BANGS=0'
    js=run(['node',out/'conformance.js']); assert js['stdout']==expected
    with tempfile.TemporaryDirectory(prefix='knot-codegen-view-') as folder:
        binary=Path(folder)/'conformance'
        commands.append(run(['clang','-std=c11','-O3',out/'conformance.c','-lpthread','-lm','-o',binary]))
        native=run([binary]); assert native['stdout']==expected
    (out/'conformance.stdout').write_text(expected)
    packed=run(['node',HERE/'capture-gpu.mjs'])
    record=json.loads(packed['stdout'])
    assert record['fixture']==next(x for x in existing['fixtures'] if x['name']=='cpu_frames')
    retained=json.loads((HERE/'cpu_frames.records.json').read_text())
    for field in ['fixture','root','opFields','operations','taskFields','initialTasks']:
        assert record[field]==retained[field],f'GPU packer observation changed: {field}'
    (out/'cpu_frames.records.json').write_text(packed['stdout'])
    inputs=['slot.bend','task.bend','conformance.bend','fixtures.bend','oracle.bend','gpu/check.mjs','gpu/tasks.wgsl']
    generated=['conformance.c','conformance.js','conformance.stdout','cpu_frames.records.json']
    report={'date':datetime.now(timezone.utc).isoformat(),
      'scope':'Actual upstream-generated CPU code and verbatim GPU-packer capture; no Knot emitter',
      'seed':seed,'inputs':{p:digest(PROTO/p) for p in inputs},
      'outputs':{p:digest(out/p) for p in generated},
      'harnesses':{p:digest(HERE/p) for p in ['capture-gpu.mjs','generate.py']},'commands':commands,
      'tools':{'node':run(['node','--version'])['stdout'].strip(),'bun':run(['bun','--version'])['stdout'].strip(),
        'clang':run(['clang','--version'])['stdout'].splitlines()[0]},
      'seed_execution':interpreted,'js_execution':js,'native_execution':native,'gpu_record_capture':packed,
      'gpu_execution':'not repeated; historical device evidence only; model/shader hashes and captured record observations match',
      'gpu_receipt_sha256':digest(PROTO/'receipts/gpu.json'),'status':'pass'}
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: emitted C and JavaScript both reproduce the 11-line protocol transcript; captured the existing GPU packer for cpu_frames.')


if __name__=='__main__': main()
