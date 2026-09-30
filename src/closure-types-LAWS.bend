import Base
import ./syntax.bend as S
import ./core.bend as C
import ./closure-types.bend as F

law arrow_location:
  for +domain: S.Token
  for result: S.Token
  {S.at(S.Arrow{domain,result}) == S.at(domain) : S.At}

law arrow_kind:
  for token: S.Token
  for domain: U32
  for result: U32
  {F.reusable(C.Arrow{token,domain,result}) == False{} : Bool}

law signature_end:
  for +result: S.Token
  {F.signature(Nil{},result) == result : S.Token}

law signature_step:
  for name: S.Token
  for quantity: U32
  for +domain: S.Token
  for +tail: List<&2,S.Node>
  for +result: S.Token
  {F.signature(Con{S.Parameter{name,quantity,domain},tail},result)
    == S.Arrow{domain,F.signature(tail,result)} : S.Token}

law interned_arrow_is_stable:
  for +index: U32
  for +types: List<&2,C.Datatype>
  for name: S.Token
  for domain: U32
  for result: U32
  {F.append(Some{index},types,name,domain,result)
    == Done{F.Interned{types,index}} : Result<S.Error,F.Interned>}

law no_type_budget:
  for mode: F.Mode
  for +tokens: List<&2,S.Token>
  for code: String
  {F.read(0n,mode,tokens,code)
    == Fail{S.Exhausted{"parse",S.here(tokens)}} : Result<S.Error,F.Read>}

law adjacent_operator:
  for left: String
  for right: String
  {S.adjacent(S.Token{left,S.At{0,1,1,0}},S.Token{right,S.At{1,2,1,1}})
    == True{} : Bool}

law separated_operator:
  for left: String
  for right: String
  {S.adjacent(S.Token{left,S.At{0,1,1,0}},S.Token{right,S.At{2,3,1,2}})
    == False{} : Bool}

law arrow_key_ignores_spelling:
  for name: S.Token
  {F.find_arrow([C.Arrow{name,0,1}],0,1,0) == Some{0} : Maybe<&2,U32>}

law arrow_key_checks_domain:
  for name: S.Token
  {F.find_arrow([C.Arrow{name,0,1}],1,1,0) == None{} : Maybe<&2,U32>}

law arrow_key_checks_result:
  for name: S.Token
  {F.find_arrow([C.Arrow{name,0,1}],0,0,0) == None{} : Maybe<&2,U32>}
