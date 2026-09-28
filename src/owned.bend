import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./ownership.bend as O
import ./heap-code.bend as A
import ./heap.bend as H
import ./wasm-bytes.bend as W

type Context is Data:
  Context{types: List<&2,C.Datatype>, functions: List<&2,C.Function>, layouts: List<&2,O.Layout>, base: U32}
type Scope is Data:
  Scope{locals: List<&2,O.Local>, next: U32, future: List<&2,U32>, tail: Bool}
type Code is Data:
  Code{instructions: List<&2,A.Instruction>, next: U32}
type Finish is Data:
  Call{index: U32, tail: Bool}
  Cell{layout: U32, tag: U32}
type Mode is Data:
  Expression{term: C.Term}
  Lower{term: C.Term}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, slots: List<&2,U32>, finish: Finish}
  Branches{terms: List<&2,C.Term>, tag: U32, source: O.Local}
  Arm{term: C.Term, source: O.Local}
  Unpack{fields: List<&2,C.Binding>, source: O.Local, offset: U32, body: C.Term}

def prepend(instructions: List<&2,A.Instruction>, code: Code) -> Code:
  match code:
    case Code{body,next}: Code{List.append(&2,A.Instruction,instructions,body),next}

def saved(initial: Code, next: U32 -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match initial:
    case Code{+instructions,+index}:
      S.choose(Result<S.Error,Code>,U32.is_lt(index,4096),u =>
        S.bind(Code,Code,next(index),body => Done{prepend(A.concat([instructions,[A.set(index)]]),body)}),u => Fail{S.Exhausted{"emit",S.At{0,0,0,0}}})

def omit(locals: List<&2,O.Local>, +level: U32) -> List<&2,O.Local>:
  match locals:
    case Nil{}: Nil{}
    case Con{+head,+tail}:
      match head:
        case O.Local{id,index,q,type_id}:
          S.choose(List<&2,O.Local>,U32.is_eq(id,level),u => tail,u => Con{head,omit(tail,level)})

def drops(locals: List<&2,O.Local>, +used: List<&2,U32>, +types: List<&2,C.Datatype>, +base: U32) -> List<&2,A.Instruction>:
  match locals:
    case Nil{}: Nil{}
    case Con{O.Local{level,+index,q,type_id},+tail}:
      S.choose(List<&2,A.Instruction>,Bool.and(O.boxed(types,type_id),Bool.not(E.contains(used,level))),u =>
        A.concat([[A.get(index),A.call(U32.add(base,3)),A.op(26)],drops(tail,used,types,base)]),u => drops(tail,used,types,base))

def reference(local: O.Local, +future: List<&2,U32>, types: List<&2,C.Datatype>, +base: U32) -> List<&2,A.Instruction>:
  match local:
    case O.Local{level,+index,q,type_id}:
      S.choose(List<&2,A.Instruction>,Bool.and(O.boxed(types,type_id),O.share(q,future,level)),u => [A.get(index),A.call(U32.add(base,1))],u => [A.get(index)])

def opening(+local: O.Local, +future: List<&2,U32>, +types: List<&2,C.Datatype>, +base: U32) -> List<&2,A.Instruction>:
  match local:
    case O.Local{level,index,q,type_id}:
      S.choose(List<&2,A.Instruction>,O.boxed(types,type_id),u =>
        A.concat([reference(local,future,types,base),[A.call(U32.add(base,2)),A.op(26)]]),u => Nil{})

def loads(slots: List<&2,U32>) -> List<&2,A.Instruction>:
  match slots:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{A.get(head),loads(tail)}

def stores(slots: List<&2,U32>, +pointer: U32, +offset: U32) -> List<&2,A.Instruction>:
  match slots:
    case Nil{}: Nil{}
    case Con{head,tail}:
      A.concat([[A.get(pointer),A.get(head),A.save(offset)],stores(tail,pointer,U32.add(offset,4))])

def finish(action: Finish, +slots: List<&2,U32>, +next: U32, +base: U32) -> Result<S.Error,Code>:
  match action:
    case Call{index,tail}:
      Done{Code{A.concat([loads(slots),[A.Index{Bool.pick(U32,tail,18,16),index}]]),next}}
    case Cell{+layout,+tag}:
      S.choose(Result<S.Error,Code>,U32.is_lt(next,4096),u =>
        Done{Code{A.concat([[A.word(layout),A.call(base),A.set(next),A.get(next),A.word(tag),A.save(0)],
          stores(slots,next,4),[A.get(next)]]),U32.add(next,1)}},u => Fail{S.Exhausted{"emit",S.At{0,0,0,0}}})

def branch(head: Code, tail: Code, index: U32, tag: U32) -> Code:
  match head tail:
    case Code{left,+a} Code{right,+b}:
      Code{A.concat([[A.get(index),A.word(tag),A.op(70),A.op(4),A.op(127)],left,[A.op(5)],right,[A.op(11)]]),Bool.pick(U32,U32.is_ge(a,b),a,b)}

def inspected(local: O.Local, next: U32 -> U32 -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match local:
    case O.Local{level,index,q,type_id}: next(index,type_id)

def argument(initial: Code, action: Finish, +slots: List<&2,U32>, next: U32 -> List<&2,U32> -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match initial action:
    case Code{+instructions,index} Call{callee,tail}:
      S.bind(Code,Code,next(index,slots),body => Done{prepend(instructions,body)})
    case Code{instructions,index} Cell{layout,tag}:
      saved(Code{instructions,index},+slot => next(U32.add(slot,1),Con{slot,slots}))

# Every recursive lowering receives exactly the holders still owned at that
# point. Future uses retain them; final uses transfer them out of the scope.
def lower(fuel: Nat, mode: Mode, +context: Context, +scope: Scope) -> Result<S.Error,Code>:
  match fuel mode context scope:
    case 0n _ _ _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+ +n Expression{+term} Context{+types,+functions,layouts,+base} Scope{+locals,+next,+future,+tail}:
      S.bind(List<&2,U32>,Code,O.needs(n,O.Term{term},functions),used =>
        +live = E.alternatives(used,future)
        S.bind(Code,Code,lower(n,Lower{term},context,Scope{O.keep(locals,live),next,future,tail}),body =>
          Done{prepend(drops(locals,live,types,base),body)}))
    case 1n+n Lower{C.Value{token,+type_id,+tag}} Context{types,functions,+layouts,+base} Scope{locals,+next,future,tail}:
      S.choose(Result<S.Error,Code>,O.boxed(types,type_id),u =>
        S.bind(U32,Code,O.layout(layouts,type_id,tag,0),layout => finish(Cell{layout,tag},Nil{},next,base)),u => Done{Code{[A.word(tag)],next}})
    case 1n+ +n Lower{C.Construct{token,type_id,+tag,+params,+args}} Context{types,functions,layouts,base} Scope{locals,next,future,tail}:
      S.bind(U32,Code,O.layout(layouts,type_id,tag,0),layout => lower(n,Arguments{args,params,Nil{},Cell{layout,tag}},context,scope))
    case 1n+n Lower{C.Reference{token,level,type_id}} Context{+types,functions,layouts,+base} Scope{locals,+next,+future,tail}:
      S.bind(O.Local,Code,O.lookup(locals,level),local => Done{Code{reference(local,future,types,base),next}})
    case 1n+ +n Lower{C.Application{token,+index,type_id,+args}} Context{types,functions,layouts,base} Scope{locals,next,future,+tail}:
      S.bind(List<&2,C.Parameter>,Code,O.signature(functions,index),+params =>
        lower(n,Arguments{args,params,Nil{},Call{index,Bool.and(tail,U32.is_le(U32.from_nat(List.length(&2,O.Local,O.parameters(params,0,0))),16))}},context,scope))
    case 1n+ +n Lower{C.Let{token,+level,+q,+type_id,+value,+body}} Context{types,+functions,layouts,base} Scope{+locals,+next,+future,+tail}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Expression{body},context,scope),u =>
        S.bind(List<&2,U32>,Code,O.needs(n,O.Term{body},functions),used =>
          +after = E.alternatives(E.remove(used,level),future)
          S.bind(Code,Code,lower(n,Expression{value},context,Scope{locals,next,after,False{}}),initial =>
            saved(initial,+index => lower(n,Expression{body},context,
              Scope{Con{O.Local{level,index,q,type_id},O.keep(locals,after)},U32.add(index,1),future,tail})))))
    case 1n+ +n Lower{C.Case{token,level,type_id,+arms}} Context{+types,functions,layouts,base} Scope{+locals,+next,+future,+tail}:
      S.bind(O.Local,Code,O.lookup(locals,level),+source =>
        inspected(source,+index => typ =>
          S.choose(Result<S.Error,Code>,O.boxed(types,typ),u =>
            saved(Code{[A.get(index),A.load(0)],next},+tag => lower(n,Branches{arms,tag,source},context,Scope{locals,U32.add(tag,1),future,tail})),u =>
            lower(n,Branches{arms,index,source},context,scope))))
    case 1n+n Lower{term} _ _: C.internal(Code,"owned-expression")
    case 1n+n Arguments{Nil{},Nil{},slots,action} Context{types,functions,layouts,base} Scope{locals,next,future,tail}:
      finish(action,List.reverse(&2,U32,slots),next,base)
    case 1n+ +n Arguments{Con{+head,+rest},Con{C.Parameter{token,q,type_id},+params},+slots,+action} Context{types,+functions,layouts,base} Scope{+locals,+next,+future,+tail}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Arguments{rest,params,slots,action},context,scope),u =>
        S.bind(List<&2,U32>,Code,O.needs(n,O.Arguments{rest,params},functions),used =>
          +after = E.alternatives(used,future)
          S.bind(Code,Code,lower(n,Expression{head},context,Scope{locals,next,after,False{}}),initial =>
            argument(initial,action,slots,index => held => lower(n,Arguments{rest,params,held,action},context,
              Scope{O.keep(locals,after),index,future,tail})))))
    case 1n+n Arguments{terms,params,slots,action} _ _: C.internal(Code,"owned-arguments")
    case 1n+n Branches{Con{head,Nil{}},tag,source} _ _: lower(n,Arm{head,source},context,scope)
    case 1n+ +n Branches{Con{C.Branch{+tag,+fields,+body},+rest},+index,+source} _ _:
      S.bind(Code,Code,lower(n,Arm{C.Branch{tag,fields,body},source},context,scope),head =>
        S.bind(Code,Code,lower(n,Branches{rest,index,source},context,scope),tail => Done{branch(head,tail,index,tag)}))
    case 1n+n Branches{terms,index,source} _ _: C.internal(Code,"owned-branches")
    case 1n+n Arm{C.Branch{tag,fields,body},O.Local{+level,index,q,type_id}} _ Scope{+locals,next,+future,tail}:
      lower(n,Unpack{fields,O.Local{level,index,q,type_id},4,body},context,
        Scope{S.choose(List<&2,O.Local>,E.contains(future,level),u => locals,u => omit(locals,level)),next,future,tail})
    case 1n+n Arm{term,source} _ _: C.internal(Code,"owned-arm")
    case 1n+n Unpack{Nil{},+source,offset,body} Context{+types,functions,layouts,+base} Scope{locals,next,+future,tail}:
      S.bind(Code,Code,lower(n,Expression{body},context,scope),body => Done{prepend(opening(source,future,types,base),body)})
    case 1n+ +n Unpack{Con{C.Binding{token,+level,+q,+type_id,param,known},+rest},+source,+offset,+body} _ Scope{+locals,+next,+future,+tail}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Unpack{rest,source,offset,body},context,scope),u =>
        inspected(source,index => typ =>
          saved(Code{[A.get(index),A.load(offset)],next},+slot => lower(n,Unpack{rest,source,U32.add(offset,4),body},context,
            Scope{Con{O.Local{level,slot,q,type_id},locals},U32.add(slot,1),future,tail}))))

def tail_calls(instructions: List<&2,A.Instruction>, +enabled: Bool) -> List<&2,A.Instruction>:
  match instructions:
    case Nil{}: Nil{}
    case Con{A.Index{+opcode,index},tail}:
      Con{A.Index{Bool.pick(U32,Bool.and(Bool.not(enabled),U32.is_eq(opcode,18)),16,opcode),index},tail_calls(tail,enabled)}
    case Con{head,tail}: Con{head,tail_calls(tail,enabled)}

# Pinned Node's arm64 baseline compiler crashes on wide return_call frames.
# These instructions occur only in source tail position; call falls through.
def function_body(value: Code, name: String, +arity: U32) -> Result<S.Error,A.Function>:
  match value:
    case Code{instructions,+next}:
      S.choose(Result<S.Error,A.Function>,U32.is_ge(next,arity),u => Done{A.FunctionCode{name,arity,U32.sub(next,arity),tail_calls(instructions,U32.is_le(next,16))}},u => C.internal(A.Function,"owned-locals"))

def entry(function: C.Function, +context: Context, +depth: Nat) -> Result<S.Error,A.Function>:
  match function:
    case C.Function{C.Signature{token,params,result},term}:
      +locals = O.parameters(params,0,0)
      +arity = U32.from_nat(List.length(&2,O.Local,locals))
      S.bind(Code,A.Function,lower(depth,Expression{term},context,Scope{locals,arity,Nil{},True{}}),code => function_body(code,S.text(token),arity))

def entries(functions: List<&2,C.Function>, +context: Context, +depth: Nat) -> Result<S.Error,List<&2,A.Function>>:
  match functions:
    case Nil{}: Done{Nil{}}
    case Con{head,+tail}:
      S.bind(A.Function,List<&2,A.Function>,entry(head,context,depth),value =>
        S.bind(List<&2,A.Function>,List<&2,A.Function>,entries(tail,context,depth),rest => Done{Con{value,rest}}))

def shapes(layouts: List<&2,O.Layout>) -> List<&2,H.Layout>:
  match layouts:
    case Nil{}: Nil{}
    case Con{O.Layout{type_id,tag,reusable,edges},tail}: Con{H.Layout{reusable,edges},shapes(tail)}

type Sections is Data:
  Sections{types: B.Builder, functions: B.Builder, exports: B.Builder, code: B.Builder}

def section_entry(function: A.Function, +index: U32, +cap: U32, parts: Sections) -> Result<S.Error,Sections>:
  match function parts:
    case A.FunctionCode{+name,+arity,locals,instructions} Sections{types,funcs,+exports,code}:
      S.bind(B.Builder,Sections,W.concat(cap,[Done{types},A.signature(arity,cap)]),types =>
        S.bind(B.Builder,Sections,W.concat(cap,[Done{funcs},W.unsigned(cap,index)]),funcs =>
          S.bind(B.Builder,Sections,S.choose(Result<S.Error,B.Builder>,String.eq(name,""),u => Done{exports},u =>
            W.concat(cap,[Done{exports},W.name(cap,name),W.bytes(cap,[0]),W.unsigned(cap,index)])),exports =>
            S.bind(B.Builder,Sections,W.concat(cap,[Done{code},A.body(function,cap)]),code => Done{Sections{types,funcs,exports,code}}))))

def sections(functions: List<&2,A.Function>, +index: U32, +cap: U32, parts: Sections) -> Result<S.Error,Sections>:
  match functions:
    case Nil{}: Done{parts}
    case Con{head,+tail}:
      S.bind(Sections,Sections,section_entry(head,index,cap,parts),next => sections(tail,U32.add(index,1),cap,next))

def export_count(functions: List<&2,A.Function>) -> U32:
  match functions:
    case Nil{}: 0
    case Con{A.FunctionCode{name,arity,locals,body},tail}: U32.add(Bool.pick(U32,String.eq(name,""),0,1),export_count(tail))

def module_bytes(parts: Sections, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match parts:
    case Sections{types,funcs,exports,code}:
      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.bytes(cap,[0,97,115,109,1,0,0,0]),W.section(cap,1,types),W.section(cap,3,funcs),H.sections(cap),
        W.section(cap,7,exports),W.section(cap,10,code)]),bytes => Done{B.finish(bytes)})

def module(+functions: List<&2,A.Function>, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  S.bind(B.Builder,List<&2,U32>,W.unsigned(cap,U32.from_nat(List.length(&2,A.Function,functions))),+count =>
    S.bind(B.Builder,List<&2,U32>,W.concat(cap,[W.unsigned(cap,U32.add(export_count(functions),1)),W.name(cap,"__heap_memory"),W.bytes(cap,[2,0])]),exports =>
      S.bind(Sections,List<&2,U32>,sections(functions,0,cap,Sections{count,count,exports,count}),parts => module_bytes(parts,cap))))

def exports(functions: List<&2,C.Function>) -> Result<S.Error,Unit>:
  match functions:
    case Nil{}: Done{Unit{}}
    case Con{C.Function{C.Signature{+token,params,result},body},+tail}:
      S.choose(Result<S.Error,Unit>,String.starts_with(S.text(token),"__heap_"),u =>
        Fail{S.Unsupported{"emit","owned-export-name",S.at(token)}},u => exports(tail))

def emit(book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match book:
    case C.Book{+types,+functions}:
      +layouts = O.layouts(types,types,0)
      +base = U32.from_nat(List.length(&2,C.Function,functions))
      S.bind(Unit,List<&2,U32>,exports(functions),u =>
        S.bind(List<&2,A.Function>,List<&2,U32>,entries(functions,Context{types,functions,layouts,base},depth),lowered =>
          module(List.append(&2,A.Function,lowered,H.functions(shapes(layouts),base)),cap)))
