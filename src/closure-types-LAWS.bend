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
