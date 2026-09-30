import Base
import ./syntax.bend as S

# Source spans record the seed's declaration events, independent of AST order.
# Term constructors may be forward references; patterns need an earlier event.
type Mode is Data:
  Declarations{items: List<&2,S.Node>}
  Body{node: S.Node}
  Arms{items: List<&2,S.Node>}
  Pattern{node: S.Node}
  Patterns{items: List<&2,S.Node>}

def earlier(left: S.Token, right: S.Token) -> Bool:
  match left right:
    case S.Token{a,S.At{p,q,l,c}} S.Token{b,S.At{r,s,m,d}}: U32.is_lt(p,r)

def known(+names: List<&2,S.Token>, +token: S.Token) -> Bool:
  match names:
    case Nil{}: False{}
    case Con{head,tail}:
      S.choose(Bool,Bool.and(String.eq(S.text(head),S.text(token)),earlier(head,token)),u =>
        True{},u => known(tail,token))

def constructors(nodes: List<&2,S.Node>, names: List<&2,S.Token>) -> List<&2,S.Token>:
  match nodes:
    case Nil{}: names
    case Con{S.Constructor{token,args},tail}: constructors(tail,Con{token,names})
    case Con{other,tail}: constructors(tail,names)

def declarations(nodes: List<&2,S.Node>, names: List<&2,S.Token>) -> List<&2,S.Token>:
  match nodes:
    case Nil{}: names
    case Con{S.Datatype{token,q,ctors},tail}: declarations(tail,constructors(ctors,names))
    case Con{S.Generic{token,params,kind,ctors},tail}: declarations(tail,constructors(ctors,names))
    case Con{other,tail}: declarations(tail,names)

def run(fuel: Nat, mode: Mode, +names: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"parse",S.here(names)}}
    case 1n+ +n Declarations{Nil{}}: Done{Unit{}}
    case 1n+ +n Declarations{Con{S.Datatype{token,q,ctors},tail}}:
      run(n,Declarations{tail},names)
    case 1n+ +n Declarations{Con{S.Generic{token,params,kind,ctors},tail}}:
      run(n,Declarations{tail},names)
    case 1n+ +n Declarations{Con{head,tail}}:
      S.bind(Unit,Unit,run(n,Body{head},names),u => run(n,Declarations{tail},names))
    case 1n+ +n Body{S.Function{token,params,result,body}}: run(n,Body{body},names)
    case 1n+ +n Body{S.TypedFunction{token,params,result,body}}: run(n,Body{body},names)
    case 1n+ +n Body{S.Binding{token,q,annot,value,body}}: run(n,Body{body},names)
    case 1n+ +n Body{S.TypedBinding{token,q,annot,value,body}}: run(n,Body{body},names)
    case 1n+ +n Body{S.Match{token,value,arms}}: run(n,Arms{arms},names)
    case 1n+ +n Body{other}: Done{Unit{}}
    case 1n+ +n Arms{Nil{}}: Done{Unit{}}
    case 1n+ +n Arms{Con{S.Arm{token,pattern,body},tail}}:
      S.bind(Unit,Unit,run(n,Pattern{pattern},names),u =>
        S.bind(Unit,Unit,run(n,Body{body},names),u => run(n,Arms{tail},names)))
    case 1n+ +n Arms{Con{other,tail}}: Fail{S.Internal{"parse","expected-arm"}}
    case 1n+ +n Pattern{S.Constructor{+token,args}}:
      S.choose(Result<S.Error,Unit>,known(names,token),u => run(n,Patterns{args},names),u =>
        Fail{S.Invalid{"parse","unknown-constructor",S.at(token)}})
    case 1n+ +n Pattern{other}: Done{Unit{}}
    case 1n+ +n Patterns{Nil{}}: Done{Unit{}}
    case 1n+ +n Patterns{Con{head,tail}}:
      S.bind(Unit,Unit,run(n,Pattern{head},names),u => run(n,Patterns{tail},names))

def validate(fuel: Nat, node: S.Node) -> Result<S.Error,Unit>:
  match node:
    case S.Sequence{+items}: run(fuel,Declarations{items},declarations(items,Nil{}))
    case _: Fail{S.Internal{"parse","expected-declarations"}}
