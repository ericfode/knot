import Base
import ./syntax.bend as S
import ./core.bend as C

# This machine interprets checked source terms, never Wasm instructions.
type Value is Data:
  Value{type_id: U32, tag: U32}
  Object{type_id: U32, tag: U32, fields: List<&2,Value>}
type Entry is Data:
  Entry{level: U32, value: Value}
type Frame is Data:
  Bind{level: U32, body: C.Term, environment: List<&2,Entry>}
  Argument{parameters: List<&2,C.Parameter>, arguments: List<&2,C.Term>, level: U32, caller: List<&2,Entry>, callee: List<&2,Entry>, body: C.Term}
  Field{type_id: U32, tag: U32, parameters: List<&2,C.Parameter>, arguments: List<&2,C.Term>, environment: List<&2,Entry>, values: List<&2,Value>}
type State is Data:
  Fields{type_id: U32, tag: U32, parameters: List<&2,C.Parameter>, arguments: List<&2,C.Term>, environment: List<&2,Entry>, values: List<&2,Value>, frames: List<&2,Frame>}
  Unpack{parameters: List<&2,C.Binding>, values: List<&2,Value>, environment: List<&2,Entry>, body: C.Term, frames: List<&2,Frame>}
  Evaluate{term: C.Term, environment: List<&2,Entry>, frames: List<&2,Frame>}
  Return{value: Value, frames: List<&2,Frame>}
  Arguments{parameters: List<&2,C.Parameter>, arguments: List<&2,C.Term>, level: U32, caller: List<&2,Entry>, callee: List<&2,Entry>, body: C.Term, frames: List<&2,Frame>}
  HostArguments{parameters: List<&2,C.Parameter>, arguments: List<&2,U32>, level: U32, environment: List<&2,Entry>, body: C.Term}

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"eval",code}}

def host(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Host{"invoke",code}}

def lookup(environment: List<&2,Entry>, +level: U32) -> Result<S.Error,Value>:
  match environment:
    case Nil{}: internal(Value,"missing-level")
    case Con{Entry{id,+value},+tail}:
      S.choose(Result<S.Error,Value>,U32.is_eq(id,level),u => Done{value},u => lookup(tail,level))

def function_at(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,C.Function>:
  match functions:
    case Nil{}: internal(C.Function,"function-index")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Function>,U32.is_eq(index,0),u => Done{head},u => function_at(tail,U32.sub(index,1)))

def function_named(functions: List<&2,C.Function>, +name: String) -> Result<S.Error,C.Function>:
  match functions:
    case Nil{}: host(C.Function,"unknown-export")
    case Con{+head,+tail}:
      match head:
        case C.Function{C.Signature{token,params,result},body}:
          S.choose(Result<S.Error,C.Function>,String.eq(S.text(token),name),u => Done{head},u => function_named(tail,name))

def select(arms: List<&2,C.Term>, +tag: U32) -> Result<S.Error,C.Term>:
  match arms:
    case Nil{}: internal(C.Term,"missing-arm")
    case Con{+head,+tail}:
      match head:
        case C.Branch{pattern,fields,body}:
          S.choose(Result<S.Error,C.Term>,U32.is_eq(tag,pattern),u => Done{head},u => select(tail,tag))
        case _: internal(C.Term,"arm-node")

def select_value(value: Value, arms: List<&2,C.Term>) -> Result<S.Error,C.Term>:
  match value:
    case Value{type_id,tag}: select(arms,tag)
    case Object{type_id,tag,fields}: select(arms,tag)

def enter_branch(value: Value, branch: C.Term, env: List<&2,Entry>, frames: List<&2,Frame>) -> Result<S.Error,State>:
  match value branch:
    case Value{typ,tag} C.Branch{pattern,Nil{},body}: Done{Evaluate{body,env,frames}}
    case Object{typ,tag,values} C.Branch{pattern,params,body}: Done{Unpack{params,values,env,body,frames}}
    case _ _: internal(State,"branch-value")

def enter(function: C.Function, args: List<&2,C.Term>, caller: List<&2,Entry>, frames: List<&2,Frame>) -> State:
  match function:
    case C.Function{C.Signature{token,params,result},body}: Arguments{params,args,0,caller,Nil{},body,frames}

def host_fields(fields: List<&2,C.Parameter>) -> Result<S.Error,Unit>:
  match fields:
    case Nil{}: Done{Unit{}}
    case Con{head,tail}: host(Unit,"structured-argument")

def host_constructor(ctors: List<&2,C.Constructor>, +tag: U32) -> Result<S.Error,Unit>:
  match ctors:
    case Nil{}: host(Unit,"argument-range")
    case Con{C.Constructor{token,+fields},+tail}:
      S.choose(Result<S.Error,Unit>,U32.is_eq(tag,0),u => host_fields(fields),u => host_constructor(tail,U32.sub(tag,1)))

def enum_tag(types: List<&2,C.Datatype>, +index: U32, +tag: U32) -> Result<S.Error,Unit>:
  match types:
    case Nil{}: internal(Unit,"type-index")
    case Con{C.Datatype{name,data,+ctors},+tail}:
      S.choose(Result<S.Error,Unit>,U32.is_eq(index,0),u => host_constructor(ctors,tag),u => enum_tag(tail,U32.sub(index,1),tag))

def host_argument(args: List<&2,U32>, type_id: U32, types: List<&2,C.Datatype>, next: U32 -> Result<S.Error,State>) -> Result<S.Error,State>:
  match args:
    case Nil{}: host(State,"argument-arity")
    case Con{+tag,tail}:
      S.bind(Unit,State,enum_tag(types,type_id,tag),u => next(tag))

def drop_argument(args: List<&2,U32>) -> List<&2,U32>:
  match args:
    case Nil{}: Nil{}
    case Con{head,tail}: tail

def unpack_live(values: List<&2,Value>, level: U32, params: List<&2,C.Binding>, env: List<&2,Entry>, body: C.Term, frames: List<&2,Frame>) -> Result<S.Error,State>:
  match values:
    case Nil{}: internal(State,"missing-field")
    case Con{value,rest}: Done{Unpack{params,rest,Con{Entry{level,value},env},body,frames}}

# Each step either advances one source-machine transition or reports a failure.
# Erased initializers and arguments are skipped before entering Evaluate.
def step(state: State, +book: C.Book) -> Result<S.Error,State>:
  match state book:
    case Evaluate{C.Value{token,type_id,tag},env,frames} _:
      Done{Return{Value{type_id,tag},frames}}
    case Evaluate{C.Construct{token,type_id,tag,params,args},env,frames} _:
      Done{Fields{type_id,tag,params,args,env,Nil{},frames}}
    case Evaluate{C.Reference{token,level,type_id},env,+frames} _:
      S.bind(Value,State,lookup(env,level),value => Done{Return{value,frames}})
    case Evaluate{C.Application{token,index,type_id,+args},+env,+frames} C.Book{types,functions}:
      S.bind(C.Function,State,function_at(functions,index),function => Done{enter(function,args,env,frames)})
    case Evaluate{C.Let{token,+level,q,type_id,+value,+body},+env,+frames} _:
      S.choose(Result<S.Error,State>,U32.is_eq(q,0),u => Done{Evaluate{body,env,frames}},u =>
        Done{Evaluate{value,env,Con{Bind{level,body,env},frames}}})
    case Evaluate{C.Case{token,level,type_id,+arms},+env,+frames} _:
      S.bind(Value,State,lookup(env,level),+value =>
        S.bind(C.Term,State,select_value(value,arms),branch => enter_branch(value,branch,env,frames)))
    case Evaluate{term,env,frames} _: internal(State,"expression-node")
    case Return{value,Con{Bind{level,body,env},rest}} _:
      Done{Evaluate{body,Con{Entry{level,value},env},rest}}
    case Return{value,Con{Argument{params,args,+level,caller,callee,body},rest}} _:
      Done{Arguments{params,args,U32.add(level,1),caller,Con{Entry{level,value},callee},body,rest}}
    case Return{value,Con{Field{type_id,tag,params,args,env,values},frames}} _:
      Done{Fields{type_id,tag,params,args,env,Con{value,values},frames}}
    case Return{value,Nil{}} _: Done{Return{value,Nil{}}}
    case Fields{type_id,tag,Nil{},Nil{},env,values,frames} _:
      Done{Return{Object{type_id,tag,List.reverse(&2,Value,values)},frames}}
    case Fields{+type_id,+tag,Con{C.Parameter{token,q,typ},+params},Con{+head,+args},+env,+values,+frames} _:
      S.choose(Result<S.Error,State>,U32.is_eq(q,0),u => Done{Fields{type_id,tag,params,args,env,values,frames}},u =>
        Done{Evaluate{head,env,Con{Field{type_id,tag,params,args,env,values},frames}}})
    case Fields{type_id,tag,params,args,env,values,frames} _: internal(State,"field-arity")
    case Unpack{Nil{},Nil{},env,body,frames} _: Done{Evaluate{body,env,frames}}
    case Unpack{Con{C.Binding{token,+level,q,typ,param,known},+params},+values,+env,+body,+frames} _:
      S.choose(Result<S.Error,State>,U32.is_eq(q,0),u => Done{Unpack{params,values,env,body,frames}},u =>
        unpack_live(values,level,params,env,body,frames))
    case Unpack{params,values,env,body,frames} _: internal(State,"pattern-arity")
    case Arguments{Nil{},Nil{},level,caller,callee,body,frames} _:
      Done{Evaluate{body,callee,frames}}
    case Arguments{Con{C.Parameter{token,q,type_id},+params},Con{+head,+args},+level,+caller,+callee,+body,+frames} _:
      S.choose(Result<S.Error,State>,U32.is_eq(q,0),u =>
        Done{Arguments{params,args,U32.add(level,1),caller,callee,body,frames}},u =>
        Done{Evaluate{head,caller,Con{Argument{params,args,level,caller,callee,body},frames}}})
    case Arguments{params,args,level,caller,callee,body,frames} _: internal(State,"call-arity")
    case HostArguments{Nil{},Nil{},level,env,body} _:
      Done{Evaluate{body,env,Nil{}}}
    case HostArguments{Con{C.Parameter{token,q,+type_id},+params},+args,+level,+env,+body} C.Book{+types,functions}:
      S.choose(Result<S.Error,State>,U32.is_eq(q,0),u =>
        Done{HostArguments{params,args,U32.add(level,1),env,body}},u => host_argument(args,type_id,types,tag =>
          Done{HostArguments{params,drop_argument(args),U32.add(level,1),Con{Entry{level,Value{type_id,tag}},env},body}}))
    case HostArguments{params,args,level,env,body} _: host(State,"argument-arity")

def run(fuel: Nat, state: State, +book: C.Book) -> Result<S.Error,Value>:
  match fuel state:
    case _ Return{value,Nil{}}: Done{value}
    case 0n _: Fail{S.Exhausted{"eval",S.At{0,0,0,0}}}
    case 1n+n _:
      S.bind(State,Value,step(state,book),next => run(n,next,book))

def start(function: C.Function, args: List<&2,U32>) -> State:
  match function:
    case C.Function{C.Signature{name,params,result},body}: HostArguments{params,args,0,Nil{},body}

def invoke(+book: C.Book, name: String, +args: List<&2,U32>, +fuel: Nat) -> Result<S.Error,Value>:
  match book:
    case C.Book{types,functions}:
      S.bind(C.Function,Value,function_named(functions,name),function => run(fuel,start(function,args),book))

def constructor_name(ctors: List<&2,C.Constructor>, +tag: U32) -> Result<S.Error,String>:
  match ctors:
    case Nil{}: internal(String,"result-tag")
    case Con{C.Constructor{+head,fields},+tail}:
      S.choose(Result<S.Error,String>,U32.is_eq(tag,0),u => Done{S.text(head)},u => constructor_name(tail,U32.sub(tag,1)))

def result_name(types: List<&2,C.Datatype>, +index: U32, +tag: U32) -> Result<S.Error,String>:
  match types:
    case Nil{}: internal(String,"result-type")
    case Con{C.Datatype{name,data,+ctors},+tail}:
      S.choose(Result<S.Error,String>,U32.is_eq(index,0),u => constructor_name(ctors,tag),u => result_name(tail,U32.sub(index,1),tag))

type Display is Data:
  One{value: Value}
  Many{values: List<&2,Value>}
  Text{text: String}

# A worklist bounds total inspection, including expansion of shared subtrees.
# Parts stay reversed until completion; the character budget bounds that output.
def render(fuel: Nat, pending: List<&2,Display>, +types: List<&2,C.Datatype>, +capacity: Nat, +parts: List<&2,String>) -> Result<S.Error,String>:
  match fuel pending:
    case _ Nil{}: Done{String.concat(List.reverse(&2,String,parts))}
    case 0n _: Fail{S.Exhausted{"inspect",S.At{0,0,0,0}}}
    case 1n+n Con{Text{+text},+tail}:
      +size = String.length(text)
      S.choose(Result<S.Error,String>,Nat.is_le(size,capacity),u =>
        render(n,tail,types,Nat.sub(capacity,size),Con{text,parts}),u => Fail{S.Exhausted{"inspect",S.At{0,0,0,0}}})
    case 1n+n Con{One{Value{type_id,tag}},+tail}:
      S.bind(String,String,result_name(types,type_id,tag),name =>
        render(n,Con{Text{String.append(name,"{}")},tail},types,capacity,parts))
    case 1n+n Con{One{Object{type_id,tag,+fields}},+tail}:
      S.bind(String,String,result_name(types,type_id,tag),name =>
        render(n,Con{Text{String.append(name,"{")},Con{Many{fields},Con{Text{"}"},tail}}},types,capacity,parts))
    case 1n+n Con{Many{Nil{}},tail}: render(n,tail,types,capacity,parts)
    case 1n+n Con{Many{Con{head,Nil{}}},tail}: render(n,Con{One{head},tail},types,capacity,parts)
    case 1n+n Con{Many{Con{head,rest}},tail}:
      render(n,Con{One{head},Con{Text{","},Con{Many{rest},tail}}},types,capacity,parts)

def display(fuel: Nat, mode: Display, types: List<&2,C.Datatype>) -> Result<S.Error,String>:
  render(fuel,[mode],types,65536n,Nil{})

def identity(value: Value) -> String:
  match value:
    case Value{type_id,tag}: String.concat([U32.show(type_id),"\t",U32.show(tag),"\t"])
    case Object{type_id,tag,fields}: String.concat([U32.show(type_id),"\t",U32.show(tag),"\t"])

def describe(+value: Value, book: C.Book) -> Result<S.Error,String>:
  match book:
    case C.Book{types,functions}:
      S.bind(String,String,display(4096n,One{value},types),name => Done{String.concat(["Evaluated\t",identity(value),name])})
