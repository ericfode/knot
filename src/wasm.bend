import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./core.bend as C
import ./check.bend as K
import ./wasm-bytes.bend as W

type Local is Data:
  Local{level: U32, index: U32}
type Environment is Data:
  Environment{locals: List<&2,Local>, next: U32}
type Code is Data:
  Code{bytes: B.Builder, next: U32}
type Mode is Data:
  Expression{term: C.Term}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>}
  Branches{terms: List<&2,C.Term>, index: U32}

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"emit",code}}

def lookup(locals: List<&2,Local>, +level: U32) -> Result<S.Error,U32>:
  match locals:
    case Nil{}: internal(U32,"missing-live-local")
    case Con{Local{id,+index},+tail}:
      S.choose(Result<S.Error,U32>,U32.is_eq(id,level),u => Done{index},u => lookup(tail,level))

def signature(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,C.Signature>:
  match functions:
    case Nil{}: internal(C.Signature,"function-index")
    case Con{C.Function{+sig,body},+tail}:
      S.choose(Result<S.Error,C.Signature>,U32.is_eq(index,0),u => Done{sig},u => signature(tail,U32.sub(index,1)))

def parameters(params: List<&2,C.Parameter>, +level: U32, +index: U32, +locals: List<&2,Local>) -> Environment:
  match params:
    case Nil{}: Environment{locals,index}
    case Con{C.Parameter{token,q,type_id},+tail}:
      S.choose(Environment,U32.is_eq(q,0),u => parameters(tail,U32.add(level,1),index,locals),u =>
        parameters(tail,U32.add(level,1),U32.add(index,1),Con{Local{level,index},locals}))

def live_types(params: List<&2,C.Parameter>) -> List<&2,U32>:
  match params:
    case Nil{}: Nil{}
    case Con{C.Parameter{token,q,type_id},+tail}:
      S.choose(List<&2,U32>,U32.is_eq(q,0),u => live_types(tail),u => Con{127,live_types(tail)})

def instruction(+cap: U32, opcode: U32, index: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.bytes(cap,[opcode]),W.unsigned(cap,index)])

def constant(+cap: U32, tag: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.bytes(cap,[65]),W.positive_signed(cap,tag)])

def code(result: Result<S.Error,B.Builder>, +next: U32) -> Result<S.Error,Code>:
  S.bind(B.Builder,Code,result,bytes => Done{Code{bytes,next}})

def append(left: B.Builder, right: Code) -> Result<S.Error,Code>:
  match right:
    case Code{bytes,+next}: code(W.join(left,bytes),next)

def called(value: Code, +cap: U32, index: U32) -> Result<S.Error,Code>:
  match value:
    case Code{bytes,next}: code(W.concat(cap,[Done{bytes},instruction(cap,16,index)]),next)

def call_body(sig: C.Signature, next: List<&2,C.Parameter> -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match sig:
    case C.Signature{token,params,result}: next(params)

def after_argument(value: Code, next: U32 -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match value:
    case Code{+bytes,index}: S.bind(Code,Code,next(index),rest => append(bytes,rest))

def after_initializer(initial: Code, +cap: U32, next: U32 -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match initial:
    case Code{+bytes,+index}:
      S.choose(Result<S.Error,Code>,U32.is_lt(index,4096),u =>
        S.bind(Code,Code,next(index),body =>
          S.bind(B.Builder,Code,W.concat(cap,[Done{bytes},instruction(cap,33,index)]),prefix => append(prefix,body))),u => Fail{S.Exhausted{"emit",S.At{0,0,0,0}}})

def branch_code(head: Code, tail: Code, +cap: U32, index: U32, tag: U32) -> Result<S.Error,Code>:
  match head tail:
    case Code{left,+a} Code{right,+b}:
      code(W.concat(cap,[instruction(cap,32,index),constant(cap,tag),W.bytes(cap,[70,4,127]),Done{left},W.bytes(cap,[5]),Done{right},W.bytes(cap,[11])]),Bool.pick(U32,U32.is_ge(a,b),a,b))

# The environment maps source lexical levels to compact live Wasm locals.
# Alternative branches share the incoming map and may reuse physical locals.
def lower(fuel: Nat, mode: Mode, +functions: List<&2,C.Function>, +locals: List<&2,Local>, +next: U32, +cap: U32) -> Result<S.Error,Code>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+ +n Expression{C.Value{token,type_id,tag}}: code(constant(cap,tag),next)
    case 1n+ +n Expression{C.Reference{token,level,type_id}}:
      S.bind(U32,Code,lookup(locals,level),index => code(instruction(cap,32,index),next))
    case 1n+ +n Expression{C.Application{token,+index,type_id,+args}}:
      S.bind(C.Signature,Code,signature(functions,index),sig => call_body(sig,params =>
        S.bind(Code,Code,lower(n,Arguments{args,params},functions,locals,next,cap),value => called(value,cap,index))))
    case 1n+ +n Expression{C.Let{token,+level,q,type_id,+value,+body}}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Expression{body},functions,locals,next,cap),u =>
        S.bind(Code,Code,lower(n,Expression{value},functions,locals,next,cap),initial =>
          after_initializer(initial,cap,+index => lower(n,Expression{body},functions,Con{Local{level,index},locals},U32.add(index,1),cap))))
    case 1n+ +n Expression{C.Case{token,level,type_id,+arms}}:
      S.bind(U32,Code,lookup(locals,level),index => lower(n,Branches{arms,index},functions,locals,next,cap))
    case 1n+ +n Expression{term}: internal(Code,"expression-node")
    case 1n+ +n Arguments{Nil{},Nil{}}: Done{Code{B.empty(cap),next}}
    case 1n+ +n Arguments{Con{+head,+tail},Con{C.Parameter{token,q,type_id},+params}}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Arguments{tail,params},functions,locals,next,cap),u =>
        S.bind(Code,Code,lower(n,Expression{head},functions,locals,next,cap),value =>
          after_argument(value,index => lower(n,Arguments{tail,params},functions,locals,index,cap))))
    case 1n+ +n Arguments{terms,params}: internal(Code,"argument-arity")
    case 1n+ +n Branches{Con{C.Branch{tag,fields,body},Nil{}},index}: lower(n,Expression{body},functions,locals,next,cap)
    case 1n+ +n Branches{Con{C.Branch{+tag,fields,body},+tail},+index}:
      S.bind(Code,Code,lower(n,Expression{body},functions,locals,next,cap),head =>
        S.bind(Code,Code,lower(n,Branches{tail,index},functions,locals,next,cap),rest => branch_code(head,rest,cap,index,tag)))
    case 1n+ +n Branches{terms,index}: internal(Code,"arm-node")

def local_declarations(+cap: U32, +count: U32) -> Result<S.Error,B.Builder>:
  S.choose(Result<S.Error,B.Builder>,U32.is_eq(count,0),u => W.bytes(cap,[0]),u =>
    W.concat(cap,[W.bytes(cap,[1]),W.unsigned(cap,count),W.bytes(cap,[127])]))

def function_code(value: Code, +parameters: U32, +cap: U32) -> Result<S.Error,B.Builder>:
  match value:
    case Code{+bytes,+next}:
      S.choose(Result<S.Error,B.Builder>,U32.is_ge(next,parameters),u =>
        S.bind(B.Builder,B.Builder,W.concat(cap,[local_declarations(cap,U32.sub(next,parameters)),Done{bytes},W.bytes(cap,[11])]),body => W.sized(cap,body)),u => internal(B.Builder,"local-count"))

def body(env: Environment, +term: C.Term, +functions: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,B.Builder>:
  match env:
    case Environment{locals,+next}:
      S.bind(Code,B.Builder,lower(depth,Expression{term},functions,locals,next,cap),value => function_code(value,next,cap))

def function_type(+cap: U32, +types: List<&2,U32>) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.bytes(cap,[96]),W.unsigned(cap,U32.from_nat(List.length(&2,U32,types))),W.bytes(cap,types),W.bytes(cap,[1,127])])

type Sections is Data:
  Sections{types: B.Builder, functions: B.Builder, exports: B.Builder, code: B.Builder}

def extend_sections(old: Sections, parts: Sections) -> Result<S.Error,Sections>:
  match old parts:
    case Sections{a,b,c,d} Sections{aa,bb,cc,dd}:
      S.bind(B.Builder,Sections,W.join(a,aa),types =>
        S.bind(B.Builder,Sections,W.join(b,bb),funcs =>
          S.bind(B.Builder,Sections,W.join(c,cc),exports =>
            S.bind(B.Builder,Sections,W.join(d,dd),code => Done{Sections{types,funcs,exports,code}}))))

def entry(function: C.Function, +index: U32, +all: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,Sections>:
  match function:
    case C.Function{C.Signature{token,+params,result},term}:
      S.bind(B.Builder,Sections,function_type(cap,live_types(params)),types =>
        S.bind(B.Builder,Sections,W.unsigned(cap,index),funcs =>
          S.bind(B.Builder,Sections,W.concat(cap,[W.name(cap,S.text(token)),W.bytes(cap,[0]),W.unsigned(cap,index)]),exports =>
            S.bind(B.Builder,Sections,body(parameters(params,0,0,Nil{}),term,all,depth,cap),code => Done{Sections{types,funcs,exports,code}}))))

def entries(remaining: List<&2,C.Function>, +index: U32, +all: List<&2,C.Function>, +depth: Nat, +cap: U32, previous: Sections) -> Result<S.Error,Sections>:
  match remaining:
    case Nil{}: Done{previous}
    case Con{head,+tail}:
      S.bind(Sections,Sections,entry(head,index,all,depth,cap),parts =>
        S.bind(Sections,Sections,extend_sections(previous,parts),next => entries(tail,U32.add(index,1),all,depth,cap,next)))

def module_bytes(parts: Sections, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match parts:
    case Sections{types,funcs,exports,code}:
      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.bytes(cap,[0,97,115,109,1,0,0,0]),W.section(cap,1,types),W.section(cap,3,funcs),W.section(cap,7,exports),W.section(cap,10,code)]),result => Done{B.finish(result)})

def emit(book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match book:
    case C.Book{types,+functions}:
      S.bind(Unit,List<&2,U32>,K.enum_profile(types),u =>
      S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,U32.from_nat(List.length(&2,C.Function,functions))),+count =>
        S.bind(Sections,List<&2,U32>,entries(functions,0,functions,depth,cap,Sections{count,count,count,count}),parts => module_bytes(parts,cap))))
