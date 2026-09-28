import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./core.bend as C
import ./check.bend as K
import ./wasm-bytes.bend as W
import ./closure.bend as F

type Local is Data:
  Local{level: U32, index: U32}
type Environment is Data:
  Environment{locals: List<&2,Local>, next: U32}
type Code is Data:
  Code{bytes: B.Builder, next: U32}
type Profile is Data:
  Enum{}
  Fields{}
type Mode is Data:
  Expression{term: C.Term}
  Tail{term: C.Term}
  Dispatch{term: C.Term}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>}
  Cell{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, slots: List<&2,U32>, tag: U32}
  Branches{terms: List<&2,C.Term>, index: U32, pointer: Maybe<&2,U32>}
  Arm{term: C.Term, pointer: Maybe<&2,U32>}
  Unpack{fields: List<&2,C.Binding>, pointer: U32, offset: U32, body: C.Term}
  TailBranches{terms: List<&2,C.Term>, index: U32, pointer: Maybe<&2,U32>}
  TailArm{term: C.Term, pointer: Maybe<&2,U32>}
  TailUnpack{fields: List<&2,C.Binding>, pointer: U32, offset: U32, body: C.Term}

def fielded(constructors: List<&2,C.Constructor>) -> Bool:
  match constructors:
    case Nil{}: False{}
    case Con{C.Constructor{token,Nil{}},tail}: fielded(tail)
    case Con{C.Constructor{token,Con{head,tail}},rest}: True{}

def heap_types(types: List<&2,C.Datatype>, +index: U32) -> List<&2,U32>:
  match types:
    case Nil{}: Nil{}
    case Con{C.Datatype{token,reusable,constructors},+tail}:
      S.choose(List<&2,U32>,fielded(constructors),u => Con{index,heap_types(tail,U32.add(index,1))},u => heap_types(tail,U32.add(index,1)))
    case Con{C.Arrow{token,domain,result},tail}: heap_types(tail,U32.add(index,1))

def boxed(types: List<&2,U32>, +index: U32) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(U32.is_eq(head,index),boxed(tail,index))

# Checked cases are exhaustive; their field signatures describe the scrutinee.
# Case.type_id describes the result, which may have a different representation.
def fielded_arms(arms: List<&2,C.Term>) -> Bool:
  match arms:
    case Nil{}: False{}
    case Con{C.Branch{tag,Con{head,tail},body},rest}: True{}
    case Con{head,tail}: fielded_arms(tail)

def capability(profile: Profile, types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match profile:
    case Enum{}: K.enum_profile(types)
    case Fields{}: Done{Unit{}}

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

def tail_called(value: Code, +cap: U32, index: U32) -> Result<S.Error,Code>:
  match value:
    case Code{bytes,next}: code(W.concat(cap,[Done{bytes},instruction(cap,18,index)]),next)

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

# Cells contain the tag followed by live fields in declaration order.
# Both loads and stores use 4-byte words with natural alignment.
def memory(+cap: U32, opcode: U32, offset: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.bytes(cap,[opcode,2]),W.unsigned(cap,offset)])

def load(+cap: U32, pointer: U32, offset: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[instruction(cap,32,pointer),memory(cap,40,offset)])

def stores(slots: List<&2,U32>, +pointer: U32, +offset: U32, +cap: U32) -> Result<S.Error,B.Builder>:
  match slots:
    case Nil{}: Done{B.empty(cap)}
    case Con{slot,tail}:
      W.concat(cap,[instruction(cap,32,pointer),instruction(cap,32,slot),memory(cap,54,offset),stores(tail,pointer,U32.add(offset,4),cap)])

def allocate(+slots: List<&2,U32>, tag: U32, allocator: U32, +next: U32, +cap: U32) -> Result<S.Error,Code>:
  S.choose(Result<S.Error,Code>,U32.is_lt(next,4096),u =>
    code(W.concat(cap,[constant(cap,U32.mul(4,U32.add(1,U32.from_nat(List.length(&2,U32,slots))))),instruction(cap,16,allocator),instruction(cap,33,next),
      instruction(cap,32,next),constant(cap,tag),memory(cap,54,0),stores(slots,next,4,cap),instruction(cap,32,next)]),U32.add(next,1)),u => Fail{S.Exhausted{"emit",S.At{0,0,0,0}}})

# The environment maps source lexical levels to compact live Wasm locals.
# Alternative branches share the incoming map and may reuse physical locals.
def lower(fuel: Nat, mode: Mode, +heap: List<&2,U32>, +functions: List<&2,C.Function>, +locals: List<&2,Local>, +next: U32, +cap: U32) -> Result<S.Error,Code>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+ +n Tail{C.Application{token,+index,type_id,+args}}:
      S.bind(C.Signature,Code,signature(functions,index),sig => call_body(sig,params =>
        S.bind(Code,Code,lower(n,Arguments{args,params},heap,functions,locals,next,cap),value => tail_called(value,cap,index))))
    case 1n+ +n Tail{C.Let{token,+level,q,type_id,+value,+body}}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Tail{body},heap,functions,locals,next,cap),u =>
        S.bind(Code,Code,lower(n,Expression{value},heap,functions,locals,next,cap),initial =>
          after_initializer(initial,cap,+index => lower(n,Tail{body},heap,functions,Con{Local{level,index},locals},U32.add(index,1),cap))))
    case 1n+ +n Tail{C.Case{token,level,type_id,+arms}}:
      S.bind(U32,Code,lookup(locals,level),+index =>
        S.choose(Result<S.Error,Code>,fielded_arms(arms),u =>
          S.bind(Code,Code,code(load(cap,index,0),next),initial =>
            after_initializer(initial,cap,+tag => lower(n,TailBranches{arms,tag,Some{index}},heap,functions,locals,U32.add(tag,1),cap))),u =>
          lower(n,TailBranches{arms,index,None{}},heap,functions,locals,next,cap)))
    case 1n+ n Tail{term}: lower(n,Expression{term},heap,functions,locals,next,cap)
    case 1n+ +n Dispatch{C.Case{token,level,type_id,+arms}}:
      S.bind(U32,Code,lookup(locals,level),+index =>
        S.bind(Code,Code,code(load(cap,index,0),next),initial =>
          after_initializer(initial,cap,+tag => lower(n,TailBranches{arms,tag,Some{index}},heap,functions,locals,U32.add(tag,1),cap))))
    case 1n+ n Dispatch{term}: internal(Code,"dispatch-node")
    case 1n+ +n Expression{C.Value{token,type_id,+tag}}:
      S.choose(Result<S.Error,Code>,boxed(heap,type_id),u => allocate(Nil{},tag,U32.from_nat(List.length(&2,C.Function,functions)),next,cap),u => code(constant(cap,tag),next))
    case 1n+ +n Expression{C.Construct{token,type_id,tag,params,args}}:
      lower(n,Cell{args,params,Nil{},tag},heap,functions,locals,next,cap)
    case 1n+ +n Expression{C.Reference{token,level,type_id}}:
      S.bind(U32,Code,lookup(locals,level),index => code(instruction(cap,32,index),next))
    case 1n+ +n Expression{C.Application{token,+index,type_id,+args}}:
      S.bind(C.Signature,Code,signature(functions,index),sig => call_body(sig,params =>
        S.bind(Code,Code,lower(n,Arguments{args,params},heap,functions,locals,next,cap),value => called(value,cap,index))))
    case 1n+ +n Expression{C.Let{token,+level,q,type_id,+value,+body}}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Expression{body},heap,functions,locals,next,cap),u =>
        S.bind(Code,Code,lower(n,Expression{value},heap,functions,locals,next,cap),initial =>
          after_initializer(initial,cap,+index => lower(n,Expression{body},heap,functions,Con{Local{level,index},locals},U32.add(index,1),cap))))
    case 1n+ +n Expression{C.Case{token,level,type_id,+arms}}:
      S.bind(U32,Code,lookup(locals,level),+index =>
        S.choose(Result<S.Error,Code>,fielded_arms(arms),u =>
          S.bind(Code,Code,code(load(cap,index,0),next),initial =>
            after_initializer(initial,cap,+tag => lower(n,Branches{arms,tag,Some{index}},heap,functions,locals,U32.add(tag,1),cap))),u =>
          lower(n,Branches{arms,index,None{}},heap,functions,locals,next,cap)))
    case 1n+ +n Expression{term}: internal(Code,"expression-node")
    case 1n+ +n Arguments{Nil{},Nil{}}: Done{Code{B.empty(cap),next}}
    case 1n+ +n Arguments{Con{+head,+tail},Con{C.Parameter{token,q,type_id},+params}}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Arguments{tail,params},heap,functions,locals,next,cap),u =>
        S.bind(Code,Code,lower(n,Expression{head},heap,functions,locals,next,cap),value =>
          after_argument(value,index => lower(n,Arguments{tail,params},heap,functions,locals,index,cap))))
    case 1n+ +n Arguments{terms,params}: internal(Code,"argument-arity")
    case 1n+ +n Cell{Nil{},Nil{},slots,tag}:
      allocate(List.reverse(&2,U32,slots),tag,U32.from_nat(List.length(&2,C.Function,functions)),next,cap)
    case 1n+ +n Cell{Con{+head,+tail},Con{C.Parameter{token,q,type_id},+params},+slots,+tag}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Cell{tail,params,slots,tag},heap,functions,locals,next,cap),u =>
        S.bind(Code,Code,lower(n,Expression{head},heap,functions,locals,next,cap),initial =>
          after_initializer(initial,cap,+index => lower(n,Cell{tail,params,Con{index,slots},tag},heap,functions,locals,U32.add(index,1),cap))))
    case 1n+ +n Cell{terms,params,slots,tag}: internal(Code,"field-arity")
    case 1n+ +n Branches{Con{head,Nil{}},index,pointer}:
      lower(n,Arm{head,pointer},heap,functions,locals,next,cap)
    case 1n+ +n Branches{Con{C.Branch{+tag,+fields,+body},+tail},+index,+pointer}:
      S.bind(Code,Code,lower(n,Arm{C.Branch{tag,fields,body},pointer},heap,functions,locals,next,cap),head =>
        S.bind(Code,Code,lower(n,Branches{tail,index,pointer},heap,functions,locals,next,cap),rest => branch_code(head,rest,cap,index,tag)))
    case 1n+ +n Branches{terms,index,pointer}: internal(Code,"arm-node")
    case 1n+ +n Arm{C.Branch{tag,Nil{},body},None{}}:
      lower(n,Expression{body},heap,functions,locals,next,cap)
    case 1n+ +n Arm{C.Branch{tag,fields,body},Some{pointer}}:
      lower(n,Unpack{fields,pointer,4,body},heap,functions,locals,next,cap)
    case 1n+ +n Arm{term,pointer}: internal(Code,"field-layout")
    case 1n+ +n Unpack{Nil{},pointer,offset,body}: lower(n,Expression{body},heap,functions,locals,next,cap)
    case 1n+ +n Unpack{Con{C.Binding{token,+level,q,type_id,param,known},+tail},+pointer,+offset,+body}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Unpack{tail,pointer,offset,body},heap,functions,locals,next,cap),u =>
        S.bind(Code,Code,code(load(cap,pointer,offset),next),initial =>
          after_initializer(initial,cap,+index => lower(n,Unpack{tail,pointer,U32.add(offset,4),body},heap,functions,Con{Local{level,index},locals},U32.add(index,1),cap))))
    case 1n+ n TailBranches{Nil{},index,pointer}: code(W.bytes(cap,[0]),next)
    case 1n+ n TailBranches{Con{head,Nil{}},index,pointer}:
      lower(n,TailArm{head,pointer},heap,functions,locals,next,cap)
    case 1n+ +n TailBranches{Con{C.Branch{+tag,+fields,+body},+rest},+index,+pointer}:
      S.bind(Code,Code,lower(n,TailArm{C.Branch{tag,fields,body},pointer},heap,functions,locals,next,cap),head =>
        S.bind(Code,Code,lower(n,TailBranches{rest,index,pointer},heap,functions,locals,next,cap),tail => branch_code(head,tail,cap,index,tag)))
    case 1n+ n TailBranches{terms,index,pointer}: internal(Code,"arm-node")
    case 1n+ n TailArm{C.Branch{tag,Nil{},body},None{}}:
      lower(n,Tail{body},heap,functions,locals,next,cap)
    case 1n+ n TailArm{C.Branch{tag,fields,body},Some{pointer}}:
      lower(n,TailUnpack{fields,pointer,4,body},heap,functions,locals,next,cap)
    case 1n+ n TailArm{term,pointer}: internal(Code,"field-layout")
    case 1n+ n TailUnpack{Nil{},pointer,offset,body}: lower(n,Tail{body},heap,functions,locals,next,cap)
    case 1n+ +n TailUnpack{Con{C.Binding{token,+level,q,type_id,param,known},+rest},+pointer,+offset,+body}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,TailUnpack{rest,pointer,offset,body},heap,functions,locals,next,cap),u =>
        S.bind(Code,Code,code(load(cap,pointer,offset),next),initial =>
          after_initializer(initial,cap,+index => lower(n,TailUnpack{rest,pointer,U32.add(offset,4),body},heap,functions,Con{Local{level,index},locals},U32.add(index,1),cap))))

def local_declarations(+cap: U32, +count: U32) -> Result<S.Error,B.Builder>:
  S.choose(Result<S.Error,B.Builder>,U32.is_eq(count,0),u => W.bytes(cap,[0]),u =>
    W.concat(cap,[W.bytes(cap,[1]),W.unsigned(cap,count),W.bytes(cap,[127])]))

def function_code(value: Code, +parameters: U32, +cap: U32) -> Result<S.Error,B.Builder>:
  match value:
    case Code{+bytes,+next}:
      S.choose(Result<S.Error,B.Builder>,U32.is_ge(next,parameters),u =>
        S.bind(B.Builder,B.Builder,W.concat(cap,[local_declarations(cap,U32.sub(next,parameters)),Done{bytes},W.bytes(cap,[11])]),body => W.sized(cap,body)),u => internal(B.Builder,"local-count"))

def body(env: Environment, +term: C.Term, +heap: List<&2,U32>, +functions: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,B.Builder>:
  match env:
    case Environment{locals,+next}:
      S.bind(Code,B.Builder,lower(depth,Expression{term},heap,functions,locals,next,cap),value => function_code(value,next,cap))

def closure_body(env: Environment, +term: C.Term, +dispatch: Bool, +heap: List<&2,U32>, +functions: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,B.Builder>:
  match env:
    case Environment{locals,+next}:
      S.bind(Code,B.Builder,lower(depth,Bool.pick(Mode,dispatch,Dispatch{term},Tail{term}),heap,functions,locals,next,cap),value => function_code(value,next,cap))

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

def entry(function: C.Function, +index: U32, +exports: U32, +tails: Bool, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,Sections>:
  match function:
    case C.Function{C.Signature{+token,+params,result},+term}:
      S.bind(B.Builder,Sections,function_type(cap,live_types(params)),types =>
        S.bind(B.Builder,Sections,W.unsigned(cap,index),funcs =>
          S.bind(B.Builder,Sections,S.choose(Result<S.Error,B.Builder>,U32.is_lt(index,exports),u =>
            W.concat(cap,[W.name(cap,S.text(token)),W.bytes(cap,[0]),W.unsigned(cap,index)]),u => Done{B.empty(cap)}),names =>
            S.bind(B.Builder,Sections,S.choose(Result<S.Error,B.Builder>,tails,u =>
              closure_body(parameters(params,0,0,Nil{}),term,U32.is_ge(index,exports),heap,all,depth,cap),u =>
              body(parameters(params,0,0,Nil{}),term,heap,all,depth,cap)),code => Done{Sections{types,funcs,names,code}}))))

def entries(remaining: List<&2,C.Function>, +index: U32, +exports: U32, +tails: Bool, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32, previous: Sections) -> Result<S.Error,Sections>:
  match remaining:
    case Nil{}: Done{previous}
    case Con{head,+tail}:
      S.bind(Sections,Sections,entry(head,index,exports,tails,heap,all,depth,cap),parts =>
        S.bind(Sections,Sections,extend_sections(previous,parts),next => entries(tail,U32.add(index,1),exports,tails,heap,all,depth,cap,next)))

# Subtract before adding: every successful allocation keeps
# 0 <= bump <= 65536 without wrap.
def allocator(+cap: U32) -> Result<S.Error,B.Builder>:
  S.bind(B.Builder,B.Builder,W.concat(cap,[local_declarations(cap,1),instruction(cap,35,0),instruction(cap,33,1),
    instruction(cap,32,0),constant(cap,65536),instruction(cap,35,0),W.bytes(cap,[107,75,4,64,0,11]),
    instruction(cap,35,0),instruction(cap,32,0),W.bytes(cap,[106]),instruction(cap,36,0),instruction(cap,32,1),W.bytes(cap,[11])]),body => W.sized(cap,body))

def heap_sections(+cap: U32, heap: Bool) -> Result<S.Error,B.Builder>:
  match heap:
    case False{}: Done{B.empty(cap)}
    case True{}:
      S.bind(B.Builder,B.Builder,W.bytes(cap,[1,1,1,1]),memory =>
        S.bind(B.Builder,B.Builder,W.bytes(cap,[1,127,1,65,0,11]),global =>
          W.concat(cap,[W.section(cap,5,memory),W.section(cap,6,global)])))

def module_bytes(parts: Sections, +heap: Bool, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match parts:
    case Sections{types,funcs,exports,code}:
      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.bytes(cap,[0,97,115,109,1,0,0,0]),W.section(cap,1,types),W.section(cap,3,funcs),heap_sections(cap,heap),W.section(cap,7,exports),W.section(cap,10,code)]),result => Done{B.finish(result)})

def finish(parts: Sections, heap: Bool, index: U32, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match heap:
    case False{}: module_bytes(parts,False{},cap)
    case True{}:
      S.bind(B.Builder,List<&2,U32>,function_type(cap,[127]),types =>
        S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,index),funcs =>
          S.bind(B.Builder,List<&2,U32>,allocator(cap),code =>
            S.bind(Sections,List<&2,U32>,extend_sections(parts,Sections{types,funcs,B.empty(cap),code}),all => module_bytes(all,True{},cap)))))

def present(types: List<&2,U32>) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{head,tail}: True{}

def assembled(+heap: List<&2,U32>, +functions: List<&2,C.Function>, +exports: U32, +tails: Bool, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  +size = U32.from_nat(List.length(&2,C.Function,functions))
  S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,U32.add(size,Bool.pick(U32,present(heap),1,0))),+count =>
    S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,exports),names =>
      S.bind(Sections,List<&2,U32>,entries(functions,0,exports,tails,heap,functions,depth,cap,Sections{count,count,names,count}),parts => finish(parts,present(heap),size,cap))))

def profiled(heap: List<&2,U32>, +functions: List<&2,C.Function>, depth: Nat, cap: U32) -> Result<S.Error,List<&2,U32>>:
  assembled(heap,functions,U32.from_nat(List.length(&2,C.Function,functions)),False{},depth,cap)

def lowered(plan: F.Plan, profile: Profile, depth: Nat, cap: U32) -> Result<S.Error,List<&2,U32>>:
  match plan profile:
    case F.Plan{C.Book{types,functions},exports,heap,False{}} _: profiled(heap_types(types,0),functions,depth,cap)
    case F.Plan{book,exports,heap,True{}} Enum{}: Fail{S.Unsupported{"compile","closures",S.At{0,0,0,0}}}
    case F.Plan{C.Book{types,functions},exports,heap,True{}} Fields{}:
      assembled(List.append(&2,U32,heap,heap_types(types,0)),functions,exports,True{},depth,cap)

def emit_profile(+profile: Profile, book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match book:
    case C.Book{+types,+functions}:
      S.bind(Unit,List<&2,U32>,capability(profile,types),u =>
        S.bind(F.Plan,List<&2,U32>,F.run(C.Book{types,functions},depth),plan => lowered(plan,profile,depth,cap)))

# The original entry retains its enum-only capability and byte contract.
def emit(book: C.Book, depth: Nat, cap: U32) -> Result<S.Error,List<&2,U32>>:
  emit_profile(Enum{},book,depth,cap)
