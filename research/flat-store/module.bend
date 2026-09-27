import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ../../src/syntax.bend as S
import ../../src/wasm-bytes.bend as W
import ./assembly.bend as A
import ./runtime.bend as R

type Sections is Data:
  Sections{types: B.Builder, functions: B.Builder, exports: B.Builder, code: B.Builder}

def body(locals: U32, instructions: List<&2,A.Instruction>, +cap: U32) -> Result<S.Error,B.Builder>:
  S.bind(B.Builder,B.Builder,W.concat(cap,[W.bytes(cap,[1]),W.unsigned(cap,locals),W.bytes(cap,[127]),
    A.encode(1024n,A.InstructionList{instructions},cap),W.bytes(cap,[11])]),code => W.sized(cap,code))

def entry(function: A.Function, +index: U32, +cap: U32) -> Result<S.Error,Sections>:
  match function:
    case A.FunctionCode{name,arity,locals,instructions}:
      S.bind(B.Builder,Sections,A.signature(arity,cap),types =>
      S.bind(B.Builder,Sections,W.unsigned(cap,index),funcs =>
      S.bind(B.Builder,Sections,S.choose(Result<S.Error,B.Builder>,U32.is_eq(index,0),u => W.bytes(cap,Nil{}),u =>
        W.concat(cap,[W.name(cap,name),W.bytes(cap,[0]),W.unsigned(cap,index)])),exports =>
      S.bind(B.Builder,Sections,body(locals,instructions,cap),code => Done{Sections{types,funcs,exports,code}}))))

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
      S.bind(B.Builder,List<&2,U32>,W.bytes(cap,[1,1,2,2]),memory =>
      S.bind(B.Builder,List<&2,U32>,W.bytes(cap,[1,127,1,65,0,11]),globals =>
      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[Done{exports},W.name(cap,"memory"),W.bytes(cap,[2,0])]),exports =>
      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.bytes(cap,[0,97,115,109,1,0,0,0]),
        W.section(cap,1,types),W.section(cap,3,functions),
        W.section(cap,5,memory),W.section(cap,6,globals),
        W.section(cap,7,exports),W.section(cap,10,code)]),result => Done{B.finish(result)}))))

def emit(+cap: U32) -> Result<S.Error,List<&2,U32>>:
  S.bind(B.Builder,List<&2,U32>,W.bytes(cap,[6]),+count =>
    S.bind(Sections,List<&2,U32>,entries(R.functions(),0,cap,Sections{count,count,count,count}),parts => finish(parts,cap)))
