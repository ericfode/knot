#!/usr/bin/env python3
"""Verify published identity using a genuinely new Bend library cache."""
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import time

PKG = pathlib.Path(__file__).resolve().parents[1]
ROOT = PKG.parents[1]
closure = json.loads((PKG/'evidence/closure.json').read_text())
identity = closure['expected_hash']
returned = (PKG/'evidence/publish.stdout').read_text().splitlines()[0]
assert returned == identity
cache = pathlib.Path(tempfile.mkdtemp(prefix='remote-cache-',dir=PKG/'build'))
assert not list(cache.iterdir())
env = dict(os.environ, BEND_LIB=str(cache))
consumer = PKG/'evidence/remote-consumer.bend'
consumer.write_text('''import Base
import HASH/release.bend as CheckedRelease
import HASH/main.bend as Text
import HASH/bytes.bend as Bytes

def assert(ok: Bool, label: String) -> IO(Unit):
  match ok:
    case True{}:
      IO.print(label)
    case False{}:
      IO.die(Unit,1,"remote mismatch: " ++ label)

def equal(a: List<&2,U32>, b: List<&2,U32>) -> Bool:
  match a b:
    case Nil{} Nil{}:
      True{}
    case Con{x,xs} Con{y,ys}:
      Bool.and(U32.is_eq(x,y),equal(xs,ys))
    case Nil{} Con{y,ys}:
      False{}
    case Con{x,xs} Nil{}:
      False{}

def output(result: Result<Bytes.Error,Bytes.Builder>) -> IO(Unit):
  match result:
    case Fail{err}:
      IO.die(Unit,1,"remote byte construction failed")
    case Done{+b}:
      assert(Bool.and(equal(Bytes.finish(b),[0,97,115,109,1,0,0,0]),U32.is_eq(Bytes.length(b),8)),"REMOTE bytes:pass")

def join(a: Result<Bytes.Error,Bytes.Builder>, b: Result<Bytes.Error,Bytes.Builder>) -> IO(Unit):
  match a b:
    case Done{x} Done{y}:
      output(Bytes.compose(x,y))
    case Done{x} Fail{err}:
      IO.die(Unit,1,"remote second chunk failed")
    case Fail{err} Done{y}:
      IO.die(Unit,1,"remote first chunk failed")
    case Fail{err} Fail{other}:
      IO.die(Unit,1,"remote chunks failed")

def main() -> IO(Unit):
  do IO<Unit>:
    assert(String.eq(Text.finish(Text.character(Text.compose(Text.fragment("wasm"),Text.fragment("🙂")),Chr{10})),"wasm🙂\\n"),"REMOTE text:pass")
    join(Bytes.fragment(8,[0,97,115,109]),Bytes.fragment(4,[1,0,0,0]))
'''.replace('HASH',identity))

def run(args):
    started=time.perf_counter()
    p=subprocess.run([str(x) for x in args],env=env,cwd=ROOT,capture_output=True,text=True,timeout=180)
    r=dict(command=[str(x) for x in args],code=p.returncode,stdout=p.stdout,stderr=p.stderr,seconds=time.perf_counter()-started)
    assert p.returncode==0,r
    return r

receipt=dict(identity=identity,cache_initially_empty=True,cache=str(cache),consumer_sha256=hashlib.sha256(consumer.read_bytes()).hexdigest())
receipt['check']=run([ROOT/'scripts/bend-reference',consumer,'--check-only'])
receipt['native_build']=run([ROOT/'scripts/bend-reference',consumer,'-o',PKG/'build/remote-consumer'])
receipt['native_run']=run([PKG/'build/remote-consumer'])
receipt['js_build']=run([ROOT/'scripts/bend-reference',consumer,'-o',PKG/'build/remote-consumer.js'])
receipt['js_run']=run(['bun',PKG/'build/remote-consumer.js'])
expected='REMOTE text:pass\nREMOTE bytes:pass\n'
assert receipt['native_run']['stdout']==expected==receipt['js_run']['stdout']
receipt['fetched_files']=[]
for f in closure['closure']:
    source=cache/identity/f['path']
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest==f['sha256'],f
    receipt['fetched_files'].append(dict(path=f['path'],sha256=digest))
assert sorted(p.name for p in (cache/identity).iterdir())==sorted(f['path'] for f in closure['closure'])
(PKG/'evidence/remote.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(hash=identity,verified_files=len(receipt['fetched_files']),native='pass',js='pass')))
