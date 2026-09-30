import Base
import ./LAWS.bend as L
import ./syntax.bend as S
import ./parse.bend as P
import ./type-parse.bend as T

def L.empty_source(fuel):
  match fuel:
    case 0n: {==}
    case 1n+n: {==}

def L.word_source(extra):
  match extra:
    case 0n: {==}
    case 1n+n: {==}

def L.no_character_budget(c,tail):
  {==}

def L.no_parser_budget(tokens):
  {==}

def L.spaced_term_token(left,right,next,gap):
  %Equal.sym(Bool,T.glued(left,right),False{},gap) :
    {S.choose(Result<S.Error,P.Parsed>,_,u => next(Unit{}),u =>
      Fail{S.Unsupported{"parse","spacing",S.at(right)}})
     == Fail{S.Unsupported{"parse","spacing",S.at(right)}} : Result<S.Error,P.Parsed>}
  {==}

def L.generic_header(at):
  {==}

def L.multiple_scrutinees(at,rest):
  {==}

def L.template_binder(at,rest):
  {==}

def L.nonleading_template_binder(at,head,rest):
  {==}

def L.destructuring_binding(at,fields,rest,plain):
  %Equal.sym(Bool,Bool.or(P.starts(rest,"="),P.starts(rest,">")),False{},plain) :
    {S.choose(Result<S.Error,P.Parsed>,_,
      u => P.body_end(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},rest}),
      u => P.unsupported(Con{S.Token{"=",at},rest},"destructuring-binding"))
      == Fail{S.Unsupported{"parse","destructuring-binding",at}} : Result<S.Error,P.Parsed>}
  {==}

def L.equality_is_not_binding(at,fields,rest):
  {==}

def L.arrow_is_not_binding(at,fields,rest):
  {==}

def L.parameter_type_application(at,rest):
  {==}

def L.return_type_application(n,at,rest):
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
def L.local_import(at,rest):
  {==}

def L.hash_import(at,rest):
  {==}
