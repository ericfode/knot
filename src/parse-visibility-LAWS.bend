import Base
import ./syntax.bend as S
import ./parse-visibility.bend as V

law unknown_pattern:
  for +token: S.Token
  {V.inspect(2n,S.Constructor{token,Nil{}},Nil{},True{})
    == Fail{S.Invalid{"parse","undeclared-constructor",S.at(token)}} : Result<S.Error,Unit>}

law forward_term:
  for token: S.Token
  {V.inspect(2n,S.Constructor{token,Nil{}},Nil{},False{})
    == Done{Unit{}} : Result<S.Error,Unit>}

law declared_pattern:
  for +line: U32
  for +column: U32
  {V.inspect(2n,S.Constructor{S.Token{"Off",S.At{1,2,line,column}},Nil{}},
    [S.Token{"Off",S.At{0,1,line,column}}],True{})
    == Done{Unit{}} : Result<S.Error,Unit>}

law empty_book:
  for fuel: Nat
  for names: List<&2,S.Token>
  {V.declarations(fuel,Nil{},names) == Done{Unit{}} : Result<S.Error,Unit>}
