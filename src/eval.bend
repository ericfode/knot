import Base
import ./syntax.bend as S
import ./core.bend as C

# This machine interprets checked source terms, never Wasm instructions.
type Value is Data:
  Value{type_id: U32, tag: U32}
type Entry is Data:
  Entry{level: U32, value: Value}
type Frame is Data:
  Bind{level: U32, body: C.Term, environment: List<&2,Entry>}
  Argument{parameters: List<&2,C.Parameter>, arguments: List<&2,C.Term>, level: U32, caller: List<&2,Entry>, callee: List<&2,Entry>, body: C.Term}
type State is Data:
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
    case Con{C.Branch{pattern,+body},+tail}:
      S.choose(Result<S.Error,C.Term>,U32.is_eq(tag,pattern),u => Done{body},u => select(tail,tag))
    case _: internal(C.Term,"arm-node")

def select_value(value: Value, arms: List<&2,C.Term>) -> Result<S.Error,C.Term>:
  match value:
    case Value{type_id,tag}: select(arms,tag)

def enter(function: C.Function, args: List<&2,C.Term>, caller: List<&2,Entry>, frames: List<&2,Frame>) -> State:
  match function:
    case C.Function{C.Signature{token,params,result},body}: Arguments{params,args,0,caller,Nil{},body,frames}

def enum_tag(types: List<&2,C.Enum>, +index: U32, +tag: U32) -> Result<S.Error,Unit>:
  match types:
    case Nil{}: internal(Unit,"type-index")
    case Con{C.Enum{name,data,ctors},+tail}:
      S.choose(Result<S.Error,Unit>,U32.is_eq(index,0),u =>
        S.choose(Result<S.Error,Unit>,U32.is_lt(tag,U32.from_nat(List.length(&2,S.Token,ctors))),u => Done{Unit{}},u => host(Unit,"argument-range")),u => enum_tag(tail,U32.sub(index,1),tag))

def host_argument(args: List<&2,U32>, type_id: U32, types: List<&2,C.Enum>, next: U32 -> Result<S.Error,State>) -> Result<S.Error,State>:
  match args:
    case Nil{}: host(State,"argument-arity")
    case Con{+tag,tail}:
      S.bind(Unit,State,enum_tag(types,type_id,tag),u => next(tag))

def drop_argument(args: List<&2,U32>) -> List<&2,U32>:
  match args:
    case Nil{}: Nil{}
    case Con{head,tail}: tail

# Each step either advances one source-machine transition or reports a failure.
# Erased initializers and arguments are skipped before entering Evaluate.
def step(state: State, +book: C.Book) -> Result<S.Error,State>:
  match state book:
    case Evaluate{C.Value{token,type_id,tag},env,frames} _:
      Done{Return{Value{type_id,tag},frames}}
    case Evaluate{C.Reference{token,level,type_id},env,+frames} _:
      S.bind(Value,State,lookup(env,level),value => Done{Return{value,frames}})
    case Evaluate{C.Application{token,index,type_id,+args},+env,+frames} C.Book{types,functions}:
      S.bind(C.Function,State,function_at(functions,index),function => Done{enter(function,args,env,frames)})
    case Evaluate{C.Let{token,+level,q,type_id,+value,+body},+env,+frames} _:
      S.choose(Result<S.Error,State>,U32.is_eq(q,0),u => Done{Evaluate{body,env,frames}},u =>
        Done{Evaluate{value,env,Con{Bind{level,body,env},frames}}})
    case Evaluate{C.Case{token,level,type_id,+arms},+env,+frames} _:
      S.bind(Value,State,lookup(env,level),value =>
        S.bind(C.Term,State,select_value(value,arms),body => Done{Evaluate{body,env,frames}}))
    case Evaluate{term,env,frames} _: internal(State,"expression-node")
    case Return{value,Con{Bind{level,body,env},rest}} _:
      Done{Evaluate{body,Con{Entry{level,value},env},rest}}
    case Return{value,Con{Argument{params,args,+level,caller,callee,body},rest}} _:
      Done{Arguments{params,args,U32.add(level,1),caller,Con{Entry{level,value},callee},body,rest}}
    case Return{value,Nil{}} _: Done{Return{value,Nil{}}}
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

def constructor_name(ctors: List<&2,S.Token>, +tag: U32) -> Result<S.Error,String>:
  match ctors:
    case Nil{}: internal(String,"result-tag")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,String>,U32.is_eq(tag,0),u => Done{String.append(S.text(head),"{}")},u => constructor_name(tail,U32.sub(tag,1)))

def result_name(types: List<&2,C.Enum>, +index: U32, +tag: U32) -> Result<S.Error,String>:
  match types:
    case Nil{}: internal(String,"result-type")
    case Con{C.Enum{name,data,+ctors},+tail}:
      S.choose(Result<S.Error,String>,U32.is_eq(index,0),u => constructor_name(ctors,tag),u => result_name(tail,U32.sub(index,1),tag))

def describe(value: Value, book: C.Book) -> Result<S.Error,String>:
  match value book:
    case Value{+type_id,+tag} C.Book{types,functions}:
      S.bind(String,String,result_name(types,type_id,tag),name => Done{String.concat(["Evaluated\t",U32.show(type_id),"\t",U32.show(tag),"\t",name])})
