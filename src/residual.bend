import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E

# Constructor-expanded defaults lose the seed's residual identity. Until the
# Default core arm lands, repeated use or inspection of that affine identity
# is Unsupported. Ordinary constructor reconstruction and promotion stay intact.
type Usage is Data:
  Usage{uses: U32, inspects: Bool}
type Mode is Data:
  Term{node: S.Node}
  Nodes{nodes: List<&2,S.Node>, alternatives: Bool}

def contains(names: List<&2,S.Token>, +name: S.Token) -> Bool:
  match names:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(String.eq(S.text(head),S.text(name)),contains(tail,name))

def hide(names: List<&2,S.Token>, +name: S.Token) -> List<&2,S.Token>:
  match names:
    case Nil{}: Nil{}
    case Con{+head,+tail}:
      S.choose(List<&2,S.Token>,String.eq(S.text(head),S.text(name)),u => hide(tail,name),u => Con{head,hide(tail,name)})

def visible(bindings: List<&2,C.Binding>, +level: U32, +seen: List<&2,S.Token>) -> List<&2,S.Token>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{+token,id,q,type_id,param,known},+tail}:
      S.choose(List<&2,S.Token>,Bool.and(U32.is_eq(id,level),Bool.not(contains(seen,token))),u =>
        Con{token,visible(tail,level,Con{token,seen})},u => visible(tail,level,Con{token,seen}))

def shadow(patterns: List<&2,S.Node>, names: List<&2,S.Token>) -> List<&2,S.Token>:
  match patterns:
    case Nil{}: names
    case Con{S.Variable{token},tail}: shadow(tail,hide(names,token))
    case Con{S.Promotion{token},tail}: shadow(tail,hide(names,token))
    case Con{S.Constructor{token,args},tail}: shadow(tail,shadow(args,names))
    case Con{S.Sequence{args},tail}: shadow(tail,shadow(args,names))
    case Con{head,tail}: shadow(tail,names)

def join(left: Usage, right: Usage, alternative: Bool) -> Usage:
  match left right:
    case Usage{+a,x} Usage{+b,y}:
      Usage{S.choose(U32,alternative,u => U32.max(a,b),u => U32.min(2,U32.add(a,b))),Bool.or(x,y)}

def inspected(value: Usage) -> Usage:
  match value:
    case Usage{+uses,inspects}: Usage{uses,Bool.or(inspects,U32.is_ne(uses,0))}

def measure(fuel: Nat, mode: Mode, +names: List<&2,S.Token>, +level: U32, +origin: S.Token) -> Result<S.Error,Usage>:
  match fuel mode:
    case 0n _: C.exhausted(Usage,origin)
    case 1n+n Nodes{Nil{},alternative}: Done{Usage{0,False{}}}
    case 1n+ +n Nodes{Con{head,+tail},+alternative}:
      S.bind(Usage,Usage,measure(n,Term{head},names,level,origin),+first =>
        S.bind(Usage,Usage,measure(n,Nodes{tail,alternative},names,level,origin),rest => Done{join(first,rest,alternative)}))
    case 1n+n Term{S.Variable{token}}:
      Done{Usage{S.choose(U32,contains(names,token),u => 1,u => 0),False{}}}
    case 1n+n Term{S.Constructor{token,args}}: measure(n,Nodes{args,False{}},names,level,origin)
    case 1n+n Term{S.Call{token,args}}: measure(n,Nodes{args,False{}},names,level,origin)
    case 1n+ +n Term{S.Binding{+token,q,ann,value,+body}}:
      S.bind(Usage,Usage,S.choose(Result<S.Error,Usage>,U32.is_eq(q,0),u => Done{Usage{0,False{}}},u =>
        measure(n,Term{value},names,level,origin)),+first =>
          S.bind(Usage,Usage,measure(n,Term{body},hide(names,token),level,origin),rest => Done{join(first,rest,False{})}))
    case 1n+ +n Term{S.Match{token,value,+arms}}:
      S.bind(Usage,Usage,measure(n,Term{value},names,level,origin),+first =>
        S.bind(Usage,Usage,measure(n,Nodes{arms,True{}},names,level,origin),rest => Done{join(inspected(first),rest,False{})}))
    case 1n+n Term{S.Arm{token,pattern,body}}: measure(n,Term{body},shadow([pattern],names),level,origin)
    case 1n+n Term{S.Alias{+token,id,q,+body}}:
      measure(n,Term{body},S.choose(List<&2,S.Token>,U32.is_eq(id,level),u => Con{token,names},u => hide(names,token)),level,origin)
    case 1n+n Term{S.Sequence{nodes}}: measure(n,Nodes{nodes,False{}},names,level,origin)
    case _ _: Done{Usage{0,False{}}}

def admit(usage: Usage, token: S.Token) -> Result<S.Error,Unit>:
  match usage:
    case Usage{uses,inspects}:
      S.choose(Result<S.Error,Unit>,Bool.or(U32.is_ge(uses,2),inspects),u => C.unsupported(Unit,"residual-alias",token),u => Done{Unit{}})

# Every counted occurrence consumes the same level. Use the scope's quantity
# merge before classifying that conflict as an unimplemented residual identity.
def consumed(result: Result<S.Error,List<&2,U32>>, +usage: Usage, token: S.Token) -> Result<S.Error,Unit>:
  match result usage:
    case Fail{error} _: admit(usage,token)
    case Done{levels} Usage{uses,inspects}: admit(Usage{0,inspects},token)

def consume(+usage: Usage, +level: U32, +token: S.Token) -> Result<S.Error,Unit>:
  match usage:
    case Usage{+uses,inspects}:
      consumed(E.sequential(
        S.choose(List<&2,U32>,U32.is_ne(uses,0),u => [level],u => Nil{}),
        S.choose(List<&2,U32>,U32.is_ge(uses,2),u => [level],u => Nil{}),token),usage,token)

def guarded(binding: C.Binding, fuel: Nat, +scope: E.Scope, +token: S.Token, +level: U32, body: S.Node) -> Result<S.Error,Unit>:
  match binding scope:
    case C.Binding{name,id,q,type_id,param,Some{known}} E.Scope{bindings,next,open,+live,aliases}:
      S.choose(Result<S.Error,Unit>,Bool.and(live,U32.is_eq(q,1)),u =>
        S.bind(Usage,Unit,measure(fuel,Term{body},visible(bindings,level,Nil{}),level,token),usage => consume(usage,level,token)),u => Done{Unit{}})
    case _ _: Done{Unit{}}

def guard(+fuel: Nat, +scope: E.Scope, +token: S.Token, +level: U32, +body: S.Node) -> Result<S.Error,Unit>:
  match scope:
    case E.Scope{+bindings,next,open,live,aliases}:
      S.bind(C.Binding,Unit,E.find_level(bindings,level),binding =>
        guarded(binding,fuel,scope,token,level,body))
