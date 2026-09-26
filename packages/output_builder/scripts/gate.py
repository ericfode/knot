#!/usr/bin/env python3
"""Build/drive Bend programs; all package semantics and assertions stay in Bend."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import time

PKG = pathlib.Path(__file__).resolve().parents[1]
ROOT = PKG.parents[1]
BEND = ROOT / "scripts/bend-reference"
BUILD = PKG / "build"
EVIDENCE = PKG / "evidence"
BUILD.mkdir(exist_ok=True)
EVIDENCE.mkdir(exist_ok=True)

def command(args, timeout=120):
    start = time.perf_counter()
    p = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return dict(command=[str(x) for x in args], code=p.returncode, stdout=p.stdout,
                stderr=p.stderr, seconds=time.perf_counter()-start)

def require(r, code=0):
    if r['code'] != code:
        raise RuntimeError(json.dumps(r, indent=2))
    return r

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    results = {'source_sha256': {p.name: sha(p) for p in sorted(PKG.glob('*.bend'))}}
    results['proof'] = require(command([BEND,PKG/'PROOF.bend','--check-only']))
    results['release_check'] = require(command([BEND,PKG/'release.bend','--check-only']))
    results['native_build'] = require(command([BEND,PKG/'conformance.bend','-o',BUILD/'conformance']))
    results['native_run'] = require(command([BUILD/'conformance']))
    assert results['native_run']['stdout'].count('PASS ') == 14
    js_entry=BUILD/'js_conformance.bend'
    js_entry.write_text('import Base\nimport ../conformance.bend as T\ndef main() -> IO(Unit):\n  T.portable()\n')
    results['js_build'] = require(command([BEND,js_entry,'-o',BUILD/'conformance.js']))
    results['js_run'] = require(command(['bun',BUILD/'conformance.js']))
    assert results['js_run']['stdout'] == results['native_run']['stdout'].replace('PASS raw-char-preservation\n','')
    mutations = [
        ('discard-fragment','main.bend','  Chunk{text}\n','  Empty{}\n','text-512-triples'),
        ('reverse-compose','main.bend','  Join{left, right}\n','  Join{right, left}\n','text-512-triples'),
        ('discard-prior','main.bend','  Join{builder, Chunk{text}}','  Chunk{text}','text-512-triples'),
        ('newline-corruption','main.bend','SCon{char, SNil{}}','SCon{Chr{13}, SNil{}}','character-newline'),
        ('reverse-emit','main.bend','emit(left, emit(right, suffix))','emit(right, emit(left, suffix))','text-512-triples'),
        ('accept-256','bytes.bend','U32.is_le(h,255)','U32.is_le(h,256)','byte-success-failure-persistence'),
        ('one-past-capacity','bytes.bend','U32.is_lt(count,room)','U32.is_le(count,room)','byte-success-failure-persistence'),
        ('drop-right-bytes','bytes.bend','Join{left,right}}}','Join{left,Empty{}}}}','byte-success-failure-persistence'),
        ('wrong-remaining-room','bytes.bend','U32.is_le(m,U32.sub(cap,n))','U32.is_le(m,U32.add(cap,n))','byte-composition-order-limits'),
    ]
    results['mutations'] = []
    for name,file,old,new,witness in mutations:
        d = BUILD/'mutants'/name
        d.mkdir(parents=True,exist_ok=True)
        for source in PKG.glob('*.bend'):
            shutil.copy2(source,d/source.name)
        target=d/file
        text=target.read_text()
        assert text.count(old)==1,(name,text.count(old))
        target.write_text(text.replace(old,new))
        checked=require(command([BEND,d/file,'--check-only']))
        compiled=require(command([BEND,d/'conformance.bend','-o',d/'run']))
        ran=command([d/'run'])
        assert ran['code']==1 and 'FAIL '+witness in ran['stderr'],ran
        results['mutations'].append(dict(name=name,source_sha256=sha(target),typecheck=checked,build=compiled,run=ran,witness=witness,classification='semantic kill'))
    results['scaling'] = []
    for n in [1000,2000,4000,8000]:
        src=BUILD/f'perf_{n}.bend'
        src.write_text(f'import Base\nimport ../performance.bend as P\ndef main() -> IO(Unit):\n  P.run({n}n)\n')
        target=BUILD/f'perf_{n}'
        compiled=require(command([BEND,src,'-o',target]))
        runs=[require(command([target])) for _ in range(3)]
        expected=f'{2*n+1},{n},{4*n+1},{128*n}'
        assert all(r['stdout'].splitlines()[-1]==expected for r in runs)
        results['scaling'].append(dict(n=n,build=compiled,runs=runs,census=expected))
    (EVIDENCE/'gates.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(proof='zero holes checked separately by inspect.ts',native=14,js=13,mutants=len(mutations),scaling=[x['n'] for x in results['scaling']])))

if __name__=='__main__':
    main()
