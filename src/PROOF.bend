import Base
import ./type-parse-PROOF.bend as TypeParsing
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

def L.local_import(at,rest):
  {==}

def L.hash_import(at,rest):
  {==}
