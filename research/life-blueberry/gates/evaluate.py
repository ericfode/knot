#!/usr/bin/env python3
"""Frozen public-interface gate; no candidate edits or oracle feedback to authors."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, subprocess, time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
EXPERIMENT=HERE.parent

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('candidate',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    candidate=args.candidate.resolve()
    output=args.output.resolve()
    assert not output.exists(), 'Preserve existing evidence'
    output.parent.mkdir(parents=True,exist_ok=True)
    work=ROOT/'.local/life-blueberry/evaluation'/output.stem
    work.mkdir(parents=True,exist_ok=False)
    env={k:os.environ[k] for k in ('PATH','HOME','TMPDIR','LANG') if k in os.environ}
    report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'candidate_sha256':sha(candidate),'status':'incomplete','passed':False,'commands':[]}
    def run(label,cmd):
        before=time.monotonic()
        p=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env,text=True,capture_output=True,timeout=60)
        report['commands'].append({'label':label,'argv':list(map(str,cmd)),
            'exit':p.returncode,'seconds':time.monotonic()-before,'stdout':p.stdout,'stderr':p.stderr})
        if p.returncode: raise RuntimeError(label+' failed')
        return p.stdout
    try:
        lock=json.loads((EXPERIMENT/'preregistration.json').read_text())
        for path,digest in lock['frozen_files'].items():
            assert sha(ROOT/path)==digest, 'Changed frozen input: '+path
        report['preregistration_sha256']=sha(EXPERIMENT/'preregistration.json')
        source=candidate.read_text()
        body='\n'.join(line.split('#',1)[0] for line in source.splitlines())
        assert re.findall(r'^\s*import\s+(.+)$',body,re.M)==['Base'], 'Imports outside contract'
        assert not re.search(r'\b(?:IO|GPU|extern|foreign|axiom)\b|@|\?',body), 'Unsupported construct'
        (work/'candidate.bend').write_text(source)
        wrapper=work/'entry.bend'
        wrapper.write_text('import Base\nimport ./candidate.bend as C\n\n'
          'def call_step(w: U32, h: U32, xs: List<&2,U32>) -> List<&2,U32>:\n  C.step(w,h,xs)\n\n'
          'def call_evolve(n: Nat, w: U32, h: U32, xs: List<&2,U32>) -> List<&2,U32>:\n  C.evolve(n,w,h,xs)\n')
        report['status']='compiler-failed'
        run('check',[ROOT/'scripts/bend-reference',wrapper,'--check-only'])
        compiled=work/'compiled.mjs'
        run('compile-js',['bun',ROOT/'tests/perch-performance/compile.ts',wrapper,compiled])
        report['compiled_sha256']=sha(compiled)
        report['status']='runtime-failed'
        for runtime in ['node','bun']:
            receipt=work/(runtime+'.json')
            try:
                run(runtime,[runtime,HERE/'run.mjs',compiled,receipt])
            finally:
                if receipt.exists(): report[runtime]=json.loads(receipt.read_text())
        fixtures=json.loads(run('native-fixtures',['node','--input-type=module','-e',
          "import {nativeFixtures} from './research/life-blueberry/gates/fixtures.mjs'; console.log(JSON.stringify(nativeFixtures));"]))
        native_source=work/'native.bend'
        calls=[]
        for f in fixtures:
            cells='['+','.join(map(str,f['cells']))+']'
            calls.append('C.evolve('+str(f['turns'])+'n,'+str(f['width'])+','+str(f['height'])+','+cells+')')
        native_source.write_text('import Base\nimport ./candidate.bend as C\n\n'
          'def main() -> List<&2,List<&2,U32>>:\n  ['+',\n   '.join(calls)+']\n')
        native=work/'native'
        report['status']='native-failed'
        run('compile-native',[ROOT/'scripts/bend-reference',native_source,'-o',native])
        actual=json.loads(run('native',[native]))
        expected=[f['expected'] for f in fixtures]
        report['native']={'passed':actual==expected,'fixtures':len(fixtures),'actual':actual,'expected':expected}
        assert actual==expected,'Native full-board mismatch'
        assert sha(candidate)==report['candidate_sha256'],'Source changed during evaluation'
        report.update(status='passed',passed=True)
    except Exception as error:
        report['error']=str(error)
    report['artifacts']=str(work)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','passed','candidate_sha256')}))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
