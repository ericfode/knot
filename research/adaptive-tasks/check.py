#!/usr/bin/env python3
"""Build, run, mutate, and record; semantic definitions/oracles are in Bend."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BEND=ROOT/'scripts/bend-reference'
SOURCE=['slot.bend','task.bend','oracle.bend','fixtures.bend','LAWS.bend','PROOF.bend','conformance.bend']


def run(args):
    start=time.monotonic()
    p=subprocess.run([str(a) for a in args],cwd=ROOT,capture_output=True,text=True,timeout=60,
                     env={**os.environ,'BEND_NO_TELEMETRY':'1'})
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start}


def checked(r):
    assert r['exit']==0 and 'All terms check.' in r['stdout'],r


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    outputs=parser.add_mutually_exclusive_group()
    outputs.add_argument('--out-dir',type=Path,help='write replay evidence here (default: .local/adaptive-tasks/replay)')
    outputs.add_argument('--update-receipts',action='store_true',help='explicitly replace the retained receipts')
    parser.add_argument('--compare-receipt',type=Path,help='compare GPU observations with this historical device receipt')
    parser.add_argument('--cpu-only',action='store_true',help='run CPU gates only; never claims device acceptance')
    args=parser.parse_args()
    if args.cpu_only and args.update_receipts:
        parser.error('--cpu-only cannot replace a complete historical receipt')
    out=(args.out_dir or (HERE/'receipts' if args.update_receipts else ROOT/'.local/adaptive-tasks/replay')).resolve()
    def save(name,report):
        out.mkdir(parents=True,exist_ok=True)
        (out/name).write_text(json.dumps(report,indent=2)+'\n')
    report={'date':datetime.now(timezone.utc).isoformat(),'scope':'Bend affine slot/task protocol and handwritten WGSL probe',
            'hashes':{f:sha256((HERE/f).read_bytes()).hexdigest() for f in SOURCE+[
                'check.py','gpu/tasks.wgsl','gpu/check.mjs','gpu/observations.mjs','gpu/adapter.mjs','gpu/package.json','gpu/package-lock.json',
                'tests/affine-valid.bend','tests/affine-task-reuse.bend','tests/affine-slot-reuse.bend']}}
    reference=json.loads((HERE.parent/'execution-models/reference-hashes.json').read_text())
    for path,digest in reference['files'].items():
        assert sha256((ROOT/'.toolchain/bend-2.0.29-574b6d3'/path).read_bytes()).hexdigest()==digest,path
    report['reference']=reference
    report['proof']=run([BEND,HERE/'PROOF.bend']); checked(report['proof'])
    report['valid_control']=run([BEND,HERE/'tests/affine-valid.bend']); checked(report['valid_control'])
    report['negative_quantity']={}
    for f in ['affine-task-reuse.bend','affine-slot-reuse.bend']:
        r=run([BEND,HERE/'tests'/f]); diagnostic=r['stdout']+r['stderr']
        assert r['exit']!=0 and 'consumed more than once' in diagnostic,r
        report['negative_quantity'][f]=r
    fixtures=run([BEND,HERE/'fixtures.bend']); assert fixtures['exit']==0,fixtures
    records=[json.loads(line) for line in fixtures['stdout'].splitlines()]
    assert len(records)==10
    value=next(r['expected'] for r in records if r['name']=='cpu_frames')
    expected='\n'.join(['0,73,11',f'0,73,{value}',f'1,73,{value}',f'1,73,{value}',f'1,73,{value}',
                         '0,73,11',f'1,73,{value}','1,41,226','rejected:7,9','extracted:7','missing',''])
    report['js_conformance']=run([BEND,HERE/'conformance.bend'])
    assert report['js_conformance']['exit']==0 and report['js_conformance']['stdout']==expected,report['js_conformance']
    report['fixture_sha256']=sha256(fixtures['stdout'].encode()).hexdigest()
    report['fixtures']=records
    mutations=[
        ('wrong_tick','task.bend','1013904223','1013904224','one_tick','LCG payload update'),
        ('swapped_join','task.bend','U32.add(U32.mul(a,31),b)','U32.add(U32.mul(b,31),a)','binary_order','source-ordered result slots'),
        ('lost_destination','task.bend','case 0n Nil{}:\n      Delivered{dest,p}','case 0n Nil{}:\n      Delivered{0,p}','binary_order','delivery destination'),
        ('discard_zero_budget','task.bend','case 0n _:\n      state','case 0n _:\n      Delivered{0,OwnedWord{0}}','zero_fuel','zero budget preserves residual work'),
        ('overwrite_owned_slot','slot.bend','case Occupied{value}: Rejected{Occupied{value},x}',
         'case Occupied{value}: Inserted{Occupied{x}}','put_full','failed insertion retains old and new owners'),
    ]
    report['mutants']=[]
    with tempfile.TemporaryDirectory(prefix='knot-adaptive-laws-') as td:
        tmp=Path(td)
        for entry in ['conformance','fixtures']:
            build=run([BEND,HERE/(entry+'.bend'),'-o',tmp/entry]); assert build['exit']==0,build
            observed=run([tmp/entry]); assert observed['exit']==0,observed
            target=expected if entry=='conformance' else fixtures['stdout']
            assert observed['stdout']==target,observed
            report['native_'+entry]={'build':build,'run':observed}
        for name,file,old,new,law,observation in mutations:
            folder=tmp/name; folder.mkdir()
            for f in SOURCE: shutil.copy2(HERE/f,folder/f)
            source=(folder/file).read_text(); assert source.count(old)==1,(name,source.count(old))
            (folder/file).write_text(source.replace(old,new))
            model=run([BEND,folder/file]); checked(model)
            proof=run([BEND,folder/'PROOF.bend']); diagnostic=proof['stdout']+proof['stderr']
            assert proof['exit']!=0 and law in diagnostic and 'expected' in diagnostic and 'observed' in diagnostic,proof
            witness=run([BEND,folder/'conformance.bend'])
            assert witness['exit']==0 and witness['stdout']!=expected,witness
            report['mutants'].append({'name':name,'intended_observation':observation,'rejecting_law':law,
                'typechecks':True,'proof_rejected':True,'runtime_witness_differs':True,'diagnostic':diagnostic,'stdout':witness['stdout']})
        if args.cpu_only:
            report['status']='cpu-only'
            report['gpu']='not run; device acceptance is outstanding'
            save('cpu-checks.json',report)
            print('PASS CPU ONLY: 12 Bend laws, 10 native/JS fixtures, 11 protocol observations, 2 quantity negatives, 5 semantic mutants. Device gate not run.')
            print(out/'cpu-checks.json')
            return
        gpu_args=['node',HERE/'gpu/check.mjs','--out-dir',out]
        if args.compare_receipt: gpu_args+=['--compare-receipt',args.compare_receipt.resolve()]
        gpu=run(gpu_args)
        report['gpu_command']=gpu
        if gpu['exit']!=0:
            diagnostic=gpu['stdout']+gpu['stderr']
            report['status']='HostFailure' if 'hardware adapter unavailable' in diagnostic else 'failed'
            save('checks.failed.json',report)
        assert gpu['exit']==0,gpu
        report['gpu_receipt_sha256']=sha256((out/'gpu.json').read_bytes()).hexdigest()
        shader=(HERE/'gpu/tasks.wgsl').read_text()
        gpu_mutations=[
            ('device_swapped_join','t.left_value*31u+t.right_value','t.right_value*31u+t.left_value','ordered'),
            ('device_lost_capture','t.left_value*t.factor+t.bias','t.left_value*t.factor','serial_frames'),
            ('device_early_finish','if (t.remaining!=0u)','if (t.remaining>1u)','right_finishes_first'),
        ]
        report['gpu_mutants']=[]
        for name,old,new,witness in gpu_mutations:
            assert shader.count(old)==1,name
            path=tmp/(name+'.wgsl'); path.write_text(shader.replace(old,new))
            r=run(['node',HERE/'gpu/check.mjs',path,'--out-dir',out]); diagnostic=r['stdout']+r['stderr']
            assert r['exit']!=0 and witness+': oracle mismatch' in diagnostic,r
            report['gpu_mutants'].append({'name':name,'witness':witness,'shader_pipeline_created':True,
                'rejected_by':'actual-device result disagrees with Bend oracle','diagnostic':diagnostic})
    report['status']='pass'
    save('checks.json',report)
    print('PASS: 12 Bend laws (including arbitrary fuel composition), native/JS fixtures, 2 quantity negatives, 5 CPU and 3 actual-device semantic mutants.')
    print(report['gpu_command']['stdout'].strip())


if __name__=='__main__': main()
