import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ../../src/syntax.bend as S
import ../../src/wasm-bytes.bend as W
import ../../src/heap-code.bend as A
import ../../src/heap.bend as R

type Sections is Data:
  Sections{types: B.Builder, functions: B.Builder, exports: B.Builder, code: B.Builder}


def entry(function: A.Function, +index: U32, +cap: U32) -> Result<S.Error,Sections>:
  match function:
    case A.FunctionCode{+name,+arity,locals,instructions}:
      S.bind(B.Builder,Sections,A.signature(arity,cap),types =>
      S.bind(B.Builder,Sections,W.unsigned(cap,index),funcs =>
      S.bind(B.Builder,Sections,S.choose(Result<S.Error,B.Builder>,Bool.and(U32.is_ge(index,6),U32.is_le(index,11)),u => W.bytes(cap,Nil{}),u =>
        W.concat(cap,[W.name(cap,name),W.bytes(cap,[0]),W.unsigned(cap,index)])),exports =>
      S.bind(B.Builder,Sections,A.body(A.FunctionCode{name,arity,locals,instructions},cap),code => Done{Sections{types,funcs,exports,code}}))))

def extend(previous: Sections, next: Sections) -> Result<S.Error,Sections>:
  match previous next:
    case Sections{a,b,c,d} Sections{aa,bb,cc,dd}:
      S.bind(B.Builder,Sections,W.join(a,aa),types =>
      S.bind(B.Builder,Sections,W.join(b,bb),funcs =>
      S.bind(B.Builder,Sections,W.join(c,cc),exports =>
      S.bind(B.Builder,Sections,W.join(d,dd),code => Done{Sections{types,funcs,exports,code}}))))

def entries(functions: List<&2,A.Function>, +index: U32, +cap: U32, previous: Sections) -> Result<S.Error,Sections>:
  match functions:
    case Nil{}: Done{previous}
    case Con{head,tail}:
      S.bind(Sections,Sections,entry(head,index,cap),next =>
        S.bind(Sections,Sections,extend(previous,next),joined => entries(tail,U32.add(index,1),cap,joined)))

def finish(parts: Sections, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match parts:
    case Sections{types,functions,exports,code}:
      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[Done{exports},R.memory_export(cap)]),exports =>
        S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.bytes(cap,[0,97,115,109,1,0,0,0]),W.section(cap,1,types),W.section(cap,3,functions),R.sections(cap),W.section(cap,7,exports),W.section(cap,10,code)]),result => Done{B.finish(result)}))

def emit(+cap: U32) -> Result<S.Error,List<&2,U32>>:
  S.bind(B.Builder,List<&2,U32>,W.bytes(cap,[21]),+count =>
    S.bind(B.Builder,List<&2,U32>,W.bytes(cap,[16]),exports =>
      S.bind(Sections,List<&2,U32>,entries(R.functions([R.Layout{False{},Nil{}},R.Layout{False{},[True{}]},R.Layout{True{},Nil{}},R.Layout{True{},[True{},True{}]},R.Layout{False{},[False{},False{}]},R.Layout{False{},[False{}]}],0),0,cap,Sections{count,count,exports,count}),parts => finish(parts,cap))))

def show(result: Result<S.Error,List<&2,U32>>) -> String:
  match result:
    case Fail{error}: "failed"
    case Done{bytes}: List.show(~&2,~U32,~U32.show,bytes)

def main() -> IO(Unit): IO.print(show(emit(65536)))
