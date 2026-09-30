import Base
import ./syntax.bend as S

def before(declaration: S.At, use: S.At) -> Bool:
  match declaration use:
    case S.At{start,end,line,column} S.At{offset,stop,row,col}: U32.is_lt(start,offset)

def declared(names: List<&2,S.Token>, +token: S.Token) -> Bool:
  match names:
    case Nil{}: False{}
    case Con{+head,+tail}:
      S.choose(Bool,Bool.and(String.eq(S.text(head),S.text(token)),before(S.at(head),S.at(token))),u => True{},u => declared(tail,token))

def constructors(nodes: List<&2,S.Node>, names: List<&2,S.Token>) -> List<&2,S.Token>:
  match nodes:
    case Nil{}: names
    case Con{S.Constructor{token,fields},tail}: constructors(tail,Con{token,names})
    case Con{other,tail}: constructors(tail,names)

def collect(nodes: List<&2,S.Node>, names: List<&2,S.Token>) -> List<&2,S.Token>:
  match nodes:
    case Nil{}: names
    case Con{S.Datatype{token,data,ctors},tail}: collect(tail,constructors(ctors,names))
    case Con{other,tail}: collect(tail,names)

# Visibility follows source offsets, independently of AST list order. Ordinary
# constructor terms still retain the catalog's forward-reference behavior.
def inspect(fuel: Nat, node: S.Node, +names: List<&2,S.Token>, +pattern: Bool) -> Result<S.Error,Unit>:
  match fuel node:
    case 0n _: Fail{S.Exhausted{"parse",S.At{0,0,0,0}}}
    case 1n+ n S.Constructor{+token,fields}:
      S.choose(Result<S.Error,Unit>,Bool.and(pattern,Bool.not(declared(names,token))),u =>
        Fail{S.Invalid{"parse","undeclared-constructor",S.at(token)}},u =>
        inspect(n,S.Sequence{fields},names,pattern))
    case 1n+ n S.Call{token,args}: inspect(n,S.Sequence{args},names,False{})
    case 1n+ n S.Apply{token,function,args}: inspect(n,S.Sequence{Con{function,args}},names,False{})
    case 1n+ n S.Lambda{token,q,body}: inspect(n,body,names,False{})
    case 1n+ +n S.Binding{token,q,annotation,value,body}: inspect(n,S.Sequence{[value,body]},names,False{})
    case 1n+ n S.Match{token,value,arms}: inspect(n,S.Sequence{Con{value,arms}},names,False{})
    case 1n+ +n S.Arm{token,pat,body}:
      S.bind(Unit,Unit,inspect(n,pat,names,True{}),u => inspect(n,body,names,False{}))
    case 1n+ n S.Sequence{Nil{}}: Done{Unit{}}
    case 1n+ +n S.Sequence{Con{head,tail}}:
      S.bind(Unit,Unit,inspect(n,head,names,pattern),u => inspect(n,S.Sequence{tail},names,pattern))
    case 1n+ n _: Done{Unit{}}

def declarations(fuel: Nat, nodes: List<&2,S.Node>, +names: List<&2,S.Token>) -> Result<S.Error,Unit>:
  match fuel nodes:
    case _ Nil{}: Done{Unit{}}
    case 0n _: Fail{S.Exhausted{"parse",S.At{0,0,0,0}}}
    case 1n+ n Con{S.Datatype{token,data,ctors},tail}:
      declarations(n,tail,names)
    case 1n+ +n Con{S.Function{token,params,result,body},tail}:
      S.bind(Unit,Unit,inspect(n,body,names,False{}),u => declarations(n,tail,names))
    case 1n+ n Con{other,tail}: declarations(n,tail,names)

def book(fuel: Nat, root: S.Node) -> Result<S.Error,Unit>:
  match root:
    case S.Sequence{+nodes}: declarations(fuel,nodes,collect(nodes,Nil{}))
    case _: Fail{S.Internal{"parse","expected-book"}}
