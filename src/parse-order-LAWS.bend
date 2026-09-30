import Base
import ./syntax.bend as S
import ./parse-order.bend as O

law unseen_pattern:
  for +n: Nat
  for +token: S.Token
  for args: List<&2,S.Node>
  for +names: List<&2,S.Token>
  for absent: {O.known(names,token) == False{} : Bool}
  {O.run(1n+n,O.Pattern{S.Constructor{token,args}},names)
    == Fail{S.Invalid{"parse","unknown-constructor",S.at(token)}} : Result<S.Error,Unit>}

law registered_pattern:
  for +n: Nat
  for +token: S.Token
  for +args: List<&2,S.Node>
  for +names: List<&2,S.Token>
  for present: {O.known(names,token) == True{} : Bool}
  {O.run(1n+n,O.Pattern{S.Constructor{token,args}},names)
    == O.run(n,O.Patterns{args},names) : Result<S.Error,Unit>}

law no_order_budget:
  for mode: O.Mode
  for +names: List<&2,S.Token>
  {O.run(0n,mode,names)
    == Fail{S.Exhausted{"parse",S.here(names)}} : Result<S.Error,Unit>}
