#!/usr/bin/env python3
"""Build, run, mutate, and record; semantic definitions/oracles are in Bend."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
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
    p=subprocess.run([str(a) for a in args],cwd=ROOT,capture_output=True,text=True,timeout=60)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start}


def checked(r):
    assert r['exit']==0 and 'All terms check.' in r['stdout'],r


def main():
    report={'date':datetime.now(timezone.utc).isoformat(),'scope':'Bend affine slot/task protocol and handwritten WGSL probe',
            'hashes':{f:sha256((HERE/f).read_bytes()).hexdigest() for f in SOURCE+[
                'check.py','gpu/tasks.wgsl','gpu/check.mjs','gpu/adapter.mjs','gpu/package.json','gpu/package-lock.json',
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
        gpu=run(['node',HERE/'gpu/check.mjs']); assert gpu['exit']==0,gpu
        report['gpu_command']=gpu
        report['gpu_receipt_sha256']=sha256((HERE/'receipts/gpu.json').read_bytes()).hexdigest()
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
            r=run(['node',HERE/'gpu/check.mjs',path]); diagnostic=r['stdout']+r['stderr']
            assert r['exit']!=0 and witness+': oracle mismatch' in diagnostic,r
            report['gpu_mutants'].append({'name':name,'witness':witness,'shader_pipeline_created':True,
                'rejected_by':'actual-device result disagrees with Bend oracle','diagnostic':diagnostic})
    report['status']='pass'
    (HERE/'receipts').mkdir(exist_ok=True)
    (HERE/'receipts/checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 12 Bend laws (including arbitrary fuel composition), native/JS fixtures, 2 quantity negatives, 5 CPU and 3 actual-device semantic mutants.')
    print(report['gpu_command']['stdout'].strip())


if __name__=='__main__': main()
