import Base
import ./syntax.bend as S
import ./type-parse.bend as T
import ./type-parse.bend as P
import ./type-parse-LAWS.bend as L

def L.newline_is_not_glue(at,rest,mark):
  {==}

def L.term_argument(n,head,token,rest,close,comma):
  %Equal.sym(Bool,S.matches(token,">"),False{},close) :
    {S.choose(Result<S.Error,T.Parsed>,_,
      u => Done{T.Parsed{S.Sequence{Con{head,Nil{}}},rest}},
      u => S.choose(Result<S.Error,T.Parsed>,S.matches(token,","),
        u => T.then(T.run(n,T.Items{},rest),tail => end => T.prepend(head,tail,end)),
        u => Fail{S.Unsupported{"parse","term-argument",S.at(token)}}))
      == Fail{S.Unsupported{"parse","term-argument",S.at(token)}} : Result<S.Error,T.Parsed>}
  %Equal.sym(Bool,S.matches(token,","),False{},comma) :
    {S.choose(Result<S.Error,T.Parsed>,_,
      u => T.then(T.run(n,T.Items{},rest),tail => end => T.prepend(head,tail,end)),
      u => Fail{S.Unsupported{"parse","term-argument",S.at(token)}})
      == Fail{S.Unsupported{"parse","term-argument",S.at(token)}} : Result<S.Error,T.Parsed>}
  {==}

def L.marked_binder(fuel,q,name,at,rest,word,marked):
  %Equal.sym(Bool,S.identifier(name),True{},word) :
    {S.choose(Result<S.Error,T.Parsed>,_,
      u => S.choose(Result<S.Error,T.Parsed>,U32.is_eq(q,1),
        u => Done{T.Parsed{S.TypedParameter{name,0,S.QuantType{name}},Con{S.Token{",",at},rest}}},
        u => T.invalid(Con{S.Token{",",at},rest},"parameter")),
      u => T.invalid(Con{name,Con{S.Token{",",at},rest}},"parameter"))
      == Fail{S.Invalid{"parse","parameter",at}} : Result<S.Error,T.Parsed>}
  %Equal.sym(Bool,U32.is_eq(q,1),False{},marked) :
    {S.choose(Result<S.Error,T.Parsed>,_,
      u => Done{T.Parsed{S.TypedParameter{name,0,S.QuantType{name}},Con{S.Token{",",at},rest}}},
      u => T.invalid(Con{S.Token{",",at},rest},"parameter"))
      == Fail{S.Invalid{"parse","parameter",at}} : Result<S.Error,T.Parsed>}
  {==}
def L.spaced_quantity(token,value,rest,gap):
  %Equal.sym(Bool,P.glued(token,value),False{},gap) :
    {S.choose(Result<S.Error,P.Parsed>,_,u => P.literal(token,value,rest),u => P.spaced(Con{value,rest}))
     == Fail{S.Unsupported{"parse","spacing",S.at(value)}} : Result<S.Error,P.Parsed>}
  {==}
