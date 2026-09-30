import Base
import ./syntax.bend as S

# The parse CLI checks the seed's declaration-event restrictions too. The
# checked pipeline retains its existing check-phase diagnostics for these forms.
type Mode is Data:
  Term{node: S.Node, pattern: Bool}
  Nodes{nodes: List<&2,S.Node>, pattern: Bool}

def start(token: S.Token) -> U32:
  match token:
    case S.Token{text,S.At{lo,hi,line,column}}: lo

def constructors(nodes: List<&2,S.Node>) -> List<&2,S.Node>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Datatype{name,data,ctors},tail}: List.append(&2,S.Node,ctors,constructors(tail))
    case Con{head,tail}: constructors(tail)

def arity(ctors: List<&2,S.Node>, +name: S.Token) -> Maybe<&2,Nat>:
  match ctors:
    case Nil{}: None{}
    case Con{S.Constructor{+token,fields},+tail}:
      S.choose(Maybe<&2,Nat>,Bool.and(String.eq(S.text(token),S.text(name)),U32.is_lt(start(token),start(name))),u =>
        Some{List.length(&2,S.Node,fields)},u => arity(tail,name))
    case Con{head,tail}: arity(tail,name)

def binder(found: Maybe<&2,Nat>, token: S.Token) -> Result<S.Error,Unit>:
  match found:
    case None{}: Done{Unit{}}
    case Some{n}: Fail{S.Invalid{"parse","constructor-pattern-binder",S.at(token)}}

def constructor(found: Maybe<&2,Nat>, +token: S.Token, args: List<&2,S.Node>) -> Result<S.Error,Unit>:
  match found:
    case None{}: Fail{S.Invalid{"parse","unknown-constructor",S.at(token)}}
    case Some{n}:
      S.choose(Result<S.Error,Unit>,Nat.is_eq(n,List.length(&2,S.Node,args)),u => Done{Unit{}},u =>
        Fail{S.Invalid{"parse","pattern-arity",S.at(token)}})

def scan(fuel: Nat, mode: Mode, +ctors: List<&2,S.Node>, +origin: S.At) -> Result<S.Error,Unit>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"parse",origin}}
    case 1n+n Nodes{Nil{},pattern}: Done{Unit{}}
    case 1n+ +n Nodes{Con{head,+tail},+pattern}:
      S.bind(Unit,Unit,scan(n,Term{head,pattern},ctors,origin),u => scan(n,Nodes{tail,pattern},ctors,origin))
    case 1n+n Term{S.Variable{+token},pattern}:
      S.choose(Result<S.Error,Unit>,pattern,u => binder(arity(ctors,token),token),u => Done{Unit{}})
    case 1n+n Term{S.Promotion{+token},pattern}: binder(arity(ctors,token),token)
    case 1n+ +n Term{S.Constructor{+token,+args},+pattern}:
      S.bind(Unit,Unit,S.choose(Result<S.Error,Unit>,pattern,u => constructor(arity(ctors,token),token,args),u => Done{Unit{}}),u =>
        scan(n,Nodes{args,pattern},ctors,S.at(token)))
    case 1n+n Term{S.Call{+token,+args},pattern}:
      S.choose(Result<S.Error,Unit>,pattern,u => Fail{S.Invalid{"parse","pattern-form",S.at(token)}},u =>
        scan(n,Nodes{args,False{}},ctors,S.at(token)))
    case 1n+ +n Term{S.Binding{+token,q,ann,value,+body},pattern}:
      S.bind(Unit,Unit,scan(n,Term{value,False{}},ctors,S.at(token)),u => scan(n,Term{body,False{}},ctors,S.at(token)))
    case 1n+n Term{S.Match{token,value,arms},pattern}: scan(n,Nodes{arms,False{}},ctors,S.at(token))
    case 1n+ +n Term{S.Arm{+token,pattern,+body},ignored}:
      S.bind(Unit,Unit,scan(n,Term{pattern,True{}},ctors,S.at(token)),u => scan(n,Term{body,False{}},ctors,S.at(token)))
    case 1n+n Term{S.Function{token,params,result,body},pattern}: scan(n,Term{body,False{}},ctors,S.at(token))
    case 1n+n Term{S.Sequence{nodes},pattern}: scan(n,Nodes{nodes,pattern},ctors,origin)
    case _ _: Done{Unit{}}

def validate(depth: Nat, root: S.Node) -> Result<S.Error,Unit>:
  match root:
    case S.Sequence{+nodes}: scan(depth,Nodes{nodes,False{}},constructors(nodes),S.At{0,0,1,0})
    case _: Fail{S.Internal{"parse","book-node"}}
