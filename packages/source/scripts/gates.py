#!/usr/bin/env python3
"""Build/test orchestration only. All package semantics and oracles are Bend."""
import hashlib,json,pathlib,subprocess,time,statistics,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3]
PKG=ROOT/'packages/source'; BUILD=PKG/'build'; RECEIPTS=PKG/'receipts'
BEND=ROOT/'scripts/bend-reference'
BUILD.mkdir(exist_ok=True); RECEIPTS.mkdir(exist_ok=True)
def run(args):
 t=time.perf_counter(); p=subprocess.run(list(map(str,args)),cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 return {'code':p.returncode,'output':p.stdout,'seconds':time.perf_counter()-t}
def checked(args):
 r=run(args)
 if r['code']: raise RuntimeError(json.dumps(r))
 return r
def hashes(): return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PKG.glob('*.bend'))}
def gates():
 out={'sources':hashes(),'compiler':'2.0.29','revision':'574b6d39a235b539eb19a5c532993a0abb3d11ad'}
 out['proof']=checked([BEND,PKG/'PROOF.bend','--check-only'])
 for backend in ['native','js']:
  binary=BUILD/('conformance.js' if backend=='js' else 'conformance')
  out[backend+'_build']=checked([BEND,PKG/'conformance.bend','-o',binary])
  out[backend]=checked((['bun',binary] if backend=='js' else [binary]))
  assert out[backend]['output'].strip()=='1', out[backend]
 binary=BUILD/'invalid_scalars';checked([BEND,PKG/'tests/invalid_scalars.bend','-o',binary]);out['native_invalid_scalars']=checked([binary]);assert out['native_invalid_scalars']['output'].strip()=='1'
 (RECEIPTS/'gates.json').write_text(json.dumps(out,indent=2)+'\n'); return out
MUTANTS=[
 ('erase_file_on_read','(Buffer{id,n,chars,lines},char_result(r))','(Buffer{0,n,chars,lines},char_result(r))','O.get("ab",1)'),
 ('discard_content','V.Vec.push(Char,chars,c)','V.Vec.push(Char,chars,\'x\')','O.get("a😀",1)'),
 ('stale_bump','T.Cursor{id,(i + 1 : U32)}','T.Cursor{id,i}','O.bump("ab",T.Cursor{7,1},T.Cursor{7,2},Some{\'b\'})'),
 ('rewind_checkpoint','def Source.checkpoint(c: T.Cursor) -> T.Cursor:\n  c','def Source.checkpoint(c: T.Cursor) -> T.Cursor:\n  match c:\n    case T.Cursor{id,i}: T.Cursor{id,0}','O.bump("ab",T.Cursor{7,1},T.Cursor{7,2},Some{\'b\'})'),
 ('accept_foreign','restore_if(Buffer{own,n,chars,lines},i,U32.is_eq(id,own))','restore_if(Buffer{own,n,chars,lines},i,True{})','O.restore("a",T.Cursor{8,0},Fail{T.ForeignFile{}})'),
 ('empty_extraction','case Done{xs}: Done{chars_text(xs)}','case Done{xs}: Done{""}','O.extract("ab",T.Span{7,0,2},Done{"ab"})'),
 ('cr_newline',"Char.is_eq(c,'\\n'),V.Vec.push", "Bool.or(Char.is_eq(c,'\\r'),Char.is_eq(c,'\\n')),V.Vec.push",'O.locate("a\\rb",2)'),
 ('wrong_line_boundary','split_search(lo,hi,mid,U32.is_lt(pos,start))','split_search(lo,hi,mid,U32.is_le(pos,start))','O.locate("a\\nb",2)'),
 ('reject_eof','T.Cursor{id,i},U32.is_le(i,n))','T.Cursor{id,i},U32.is_lt(i,n))','O.cursor("ab",2,Done{T.Cursor{7,2}})'),
 ('noncanonical_column','offset_valid(start,col,U32.is_lt(col,(end - start : U32)))','offset_valid(start,col,U32.is_le(col,(end - start : U32)))','O.offset("a\\nb",T.Location{0,2})'),
 ('accept_surrogate','add_valid(src,c,scalar(c))','add_valid(src,c,True{})','O.rejected(T.InvalidScalar{},S.Source.new(7,SCon{Chr{55296},""}))')]
def mutations():
 report={'sources':hashes(),'mutants':[]}; main=(PKG/'main.bend').read_text()
 for name,old,new,witness in MUTANTS:
  assert main.count(old)==1,(name,main.count(old))
  dest=BUILD/'mutants'/name;dest.mkdir(parents=True,exist_ok=True)
  for p in PKG.glob('*.bend'):shutil.copyfile(p,dest/p.name)
  # Local-development dependency relocation only; published hash imports need none.
  baseline=main.replace('import ../vec/main.bend',f'import {ROOT}/packages/vec/main.bend')
  (dest/'main.bend').write_text(baseline)
  (dest/'witness.bend').write_text('import Base\nimport ./main.bend as S\nimport ./types.bend as T\nimport ./observations.bend as O\ndef main() -> U32:\n  Bool.to_u32('+witness+')\n')
  binary=dest/'witness';checked([BEND,dest/'witness.bend','-o',binary]);control=checked([binary]);assert control['output'].strip()=='1',name
  (dest/'main.bend').write_text(baseline.replace(old,new))
  typing=checked([BEND,dest/'main.bend','--check-only'])
  checked([BEND,dest/'witness.bend','-o',binary]);observed=checked([binary]);assert observed['output'].strip()=='0',(name,observed)
  report['mutants'].append({'name':name,'witness':witness,'baseline':control,'typecheck':typing,'mutant':observed,'status':'semantic-kill','sha256':hashlib.sha256((dest/'main.bend').read_bytes()).hexdigest()})
 (RECEIPTS/'mutations.json').write_text(json.dumps(report,indent=2)+'\n'); return report

def scaling():
 report={'sources':hashes(),'workload':'Build 2N alternating x/LF scalars, verify get+locate at every position including EOF. Timings include process startup, exclude compilation.','rows':[]}
 for pairs in [1024,4096,16384,65536]:
  entry=BUILD/'benchmark_entry.bend';entry.write_text(f'import Base\nimport ../benchmark.bend as B\ndef main() -> U32:\n  B.workload({pairs}n)\n')
  row={'pairs':pairs,'codepoints':pairs*2,'line_count':pairs+1,'indexed_queries':pairs*2+1,'binary_search_comparison_upper_bound':(pairs+1).bit_length()}
  for backend in ['native','js']:
   binary=BUILD/('benchmark.js' if backend=='js' else 'benchmark');checked([BEND,entry,'-o',binary]);samples=[]
   for i in range(3):
    r=checked(['bun',binary] if backend=='js' else [binary]);assert r['output'].strip()=='1',r;samples.append(r['seconds'])
   row[backend]={'seconds':samples,'median':statistics.median(samples),'verified':True}
  report['rows'].append(row)
 (RECEIPTS/'scaling.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 import sys
 for task in (sys.argv[1:] or ['gates','mutations','scaling']):
  r=globals()[task]();print(task+': PASS',flush=True)
