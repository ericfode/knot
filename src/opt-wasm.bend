import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./core.bend as C
import ./wasm.bend as W
import ./wasm-bytes.bend as Bytes

type Tail is Data:
  Return{term: C.Term}
  Branches{arms: List<&2,C.Term>, index: U32, pointer: Maybe<&2,U32>}
  Arm{branch: C.Term, pointer: Maybe<&2,U32>}
  Fields{bindings: List<&2,C.Binding>, pointer: U32, offset: U32, body: C.Term}

def called(value: W.Code, +cap: U32, index: U32) -> Result<S.Error,W.Code>:
  match value:
    case W.Code{bytes,next}: W.code(Bytes.concat(cap,[Done{bytes},W.instruction(cap,18,index)]),next)

# Only the result continuation is a tail position. Argument, initializer and
# constructor-field evaluation stay in the existing fields-profile lowerer.
def lower(fuel: Nat, tail: Tail, +self: U32, +heap: List<&2,U32>, +functions: List<&2,C.Function>, +locals: List<&2,W.Local>, +next: U32, +cap: U32) -> Result<S.Error,W.Code>:
  match fuel tail:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+ +n Return{C.Application{+token,+index,+typ,+args}}:
      S.choose(Result<S.Error,W.Code>,U32.is_eq(index,self),u =>
        S.bind(C.Signature,W.Code,W.signature(functions,index),sig => W.call_body(sig,params =>
          S.bind(W.Code,W.Code,W.lower(n,W.Arguments{args,params},heap,functions,locals,next,cap),value => called(value,cap,index)))),u =>
        W.lower(1n+n,W.Expression{C.Application{token,index,typ,args}},heap,functions,locals,next,cap))
    case 1n+ +n Return{C.Let{token,+level,q,typ,+value,+body}}:
      S.choose(Result<S.Error,W.Code>,U32.is_eq(q,0),u => lower(n,Return{body},self,heap,functions,locals,next,cap),u =>
        S.bind(W.Code,W.Code,W.lower(n,W.Expression{value},heap,functions,locals,next,cap),initial =>
          W.after_initializer(initial,cap,+index => lower(n,Return{body},self,heap,functions,Con{W.Local{level,index},locals},U32.add(index,1),cap))))
    case 1n+ +n Return{C.Case{token,level,typ,+arms}}:
      S.bind(U32,W.Code,W.lookup(locals,level),+index =>
        S.choose(Result<S.Error,W.Code>,W.fielded_arms(arms),u =>
          S.bind(W.Code,W.Code,W.code(W.load(cap,index,0),next),initial =>
            W.after_initializer(initial,cap,+tag => lower(n,Branches{arms,tag,Some{index}},self,heap,functions,locals,U32.add(tag,1),cap))),u =>
          lower(n,Branches{arms,index,None{}},self,heap,functions,locals,next,cap)))
    case 1n+ +n Return{term}: W.lower(1n+n,W.Expression{term},heap,functions,locals,next,cap)
    case 1n+ +n Branches{Con{head,Nil{}},index,pointer}:
      lower(n,Arm{head,pointer},self,heap,functions,locals,next,cap)
    case 1n+ +n Branches{Con{C.Branch{+tag,+fields,+body},+rest},+index,+pointer}:
      S.bind(W.Code,W.Code,lower(n,Arm{C.Branch{tag,fields,body},pointer},self,heap,functions,locals,next,cap),head =>
        S.bind(W.Code,W.Code,lower(n,Branches{rest,index,pointer},self,heap,functions,locals,next,cap),tail => W.branch_code(head,tail,cap,index,tag)))
    case 1n+ +n Branches{arms,index,pointer}: W.internal(W.Code,"arm-node")
    case 1n+ +n Arm{C.Branch{tag,Nil{},body},None{}}:
      lower(n,Return{body},self,heap,functions,locals,next,cap)
    case 1n+ +n Arm{C.Branch{tag,fields,body},Some{pointer}}:
      lower(n,Fields{fields,pointer,4,body},self,heap,functions,locals,next,cap)
    case 1n+ +n Arm{branch,pointer}: W.internal(W.Code,"field-layout")
    case 1n+ +n Fields{Nil{},pointer,offset,body}: lower(n,Return{body},self,heap,functions,locals,next,cap)
    case 1n+ +n Fields{Con{C.Binding{token,+level,q,typ,param,known},+rest},+pointer,+offset,+body}:
      S.choose(Result<S.Error,W.Code>,U32.is_eq(q,0),u => lower(n,Fields{rest,pointer,offset,body},self,heap,functions,locals,next,cap),u =>
        S.bind(W.Code,W.Code,W.code(W.load(cap,pointer,offset),next),initial =>
          W.after_initializer(initial,cap,+index => lower(n,Fields{rest,pointer,U32.add(offset,4),body},self,heap,functions,Con{W.Local{level,index},locals},U32.add(index,1),cap))))

def body(env: W.Environment, +term: C.Term, +self: U32, +heap: List<&2,U32>, +functions: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,B.Builder>:
  match env:
    case W.Environment{locals,+next}:
      S.bind(W.Code,B.Builder,lower(depth,Return{term},self,heap,functions,locals,next,cap),value => W.function_code(value,next,cap))

def entry(function: C.Function, +index: U32, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,W.Sections>:
  match function:
    case C.Function{C.Signature{token,+params,result},+term}:
      S.bind(B.Builder,W.Sections,W.function_type(cap,W.live_types(params)),types =>
        S.bind(B.Builder,W.Sections,Bytes.unsigned(cap,index),funcs =>
          S.bind(B.Builder,W.Sections,Bytes.concat(cap,[Bytes.name(cap,S.text(token)),Bytes.bytes(cap,[0]),Bytes.unsigned(cap,index)]),exports =>
            S.bind(B.Builder,W.Sections,body(W.parameters(params,0,0,Nil{}),term,index,heap,all,depth,cap),code => Done{W.Sections{types,funcs,exports,code}}))))

def entries(remaining: List<&2,C.Function>, +index: U32, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32, previous: W.Sections) -> Result<S.Error,W.Sections>:
  match remaining:
    case Nil{}: Done{previous}
    case Con{head,+tail}:
      S.bind(W.Sections,W.Sections,entry(head,index,heap,all,depth,cap),parts =>
        S.bind(W.Sections,W.Sections,W.extend_sections(previous,parts),next => entries(tail,U32.add(index,1),heap,all,depth,cap,next)))

def emit(book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match book:
    case C.Book{types,+functions}:
      +heap = W.heap_types(types,0)
      +size = U32.from_nat(List.length(&2,C.Function,functions))
      S.bind(B.Builder,List<&2,U32>,Bytes.unsigned(cap,U32.add(size,Bool.pick(U32,W.present(heap),1,0))),+count =>
        S.bind(B.Builder,List<&2,U32>,Bytes.unsigned(cap,size),exports =>
          S.bind(W.Sections,List<&2,U32>,entries(functions,0,heap,functions,depth,cap,W.Sections{count,count,exports,count}),parts => W.finish(parts,W.present(heap),size,cap))))
