import Base
import ./syntax.bend as S
import ./parse-order.bend as O
import ./parse-order-LAWS.bend as L

def L.unseen_pattern(n,token,args,names,absent):
  %Equal.sym(Bool,O.known(names,token),False{},absent) :
    {S.choose(Result<S.Error,Unit>,_,u => O.run(n,O.Patterns{args},names),u =>
      Fail{S.Invalid{"parse","unknown-constructor",S.at(token)}})
      == Fail{S.Invalid{"parse","unknown-constructor",S.at(token)}} : Result<S.Error,Unit>}
  {==}

def L.registered_pattern(n,token,args,names,present):
  %Equal.sym(Bool,O.known(names,token),True{},present) :
    {S.choose(Result<S.Error,Unit>,_,u => O.run(n,O.Patterns{args},names),u =>
      Fail{S.Invalid{"parse","unknown-constructor",S.at(token)}})
      == O.run(n,O.Patterns{args},names) : Result<S.Error,Unit>}
  {==}

def L.no_order_budget(mode,names):
  {==}
