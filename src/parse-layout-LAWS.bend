import Base
import ./syntax.bend as S
import ./parse.bend as P

# Layout at a header delimiter preserves its parse, including its refusal.
law datatype_colon_layout:
  for +n: Nat
  for +name: S.Token
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n+n,P.TypeKind{name},Con{S.Token{"Data",at},Con{S.Token{"\n",at},rest}})
    == P.run(1n+n,P.TypeKind{name},Con{S.Token{"Data",at},rest}) : Result<S.Error,P.Parsed>}

law generic_colon_layout:
  for +n: Nat
  for +name: S.Token
  for +params: S.Node
  for +at: S.At
  for +body: List<&2,S.Token>
  {P.run(3n+n,P.GenericKind{name,params},
      Con{S.Token{"Type",at},Con{S.Token{"\n",at},Con{S.Token{":",at},body}}})
    == P.run(3n+n,P.GenericKind{name,params},
      Con{S.Token{"Type",at},Con{S.Token{":",at},body}}) : Result<S.Error,P.Parsed>}

law result_arrow_layout:
  for +n: Nat
  for +name: S.Token
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(3n+n,P.Header{S.Token{"def",at},name},
      Con{S.Token{"(",at},Con{S.Token{")",at},Con{S.Token{"\n",at},rest}}})
    == P.run(3n+n,P.Header{S.Token{"def",at},name},
      Con{S.Token{"(",at},Con{S.Token{")",at},rest}}) : Result<S.Error,P.Parsed>}
