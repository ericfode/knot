import Base
import ./types.bend as T

law meet_associative:
  for +a: T.Q
  for +b: T.Q
  for +c: T.Q
  {T.meet(T.meet(a,b),c) == T.meet(a,T.meet(b,c)) : T.Q}

law meet_commutative:
  for +a: T.Q
  for +b: T.Q
  {T.meet(a,b) == T.meet(b,a) : T.Q}

law meet_idempotent:
  for +a: T.Q
  {T.meet(a,a) == a : T.Q}

law substitution_choice:
  for +condition: Bool
  for +a: T.Expr
  for +b: T.Expr
  for +env: List<&2,T.Binding>
  {T.subst(Bool.pick(T.Expr,condition,a,b),env) ==
   Bool.pick(T.Expr,condition,T.subst(a,env),T.subst(b,env)) : T.Expr}

law lookup_composes:
  for +first: List<&2,T.Binding>
  for +second: List<&2,T.Binding>
  for +index: U32
  {T.lookup(T.compose(first,second),index) ==
   T.subst(T.lookup(first,index),second) : T.Expr}

law substitution_composes:
  for +expr: T.Expr
  for +first: List<&2,T.Binding>
  for +second: List<&2,T.Binding>
  {T.subst(T.subst(expr,first),second) ==
   T.subst(expr,T.compose(first,second)) : T.Expr}

law substitution_identity:
  for +expr: T.Expr
  {T.subst(expr,Nil{}) == expr : T.Expr}

law literal_meet_normalizes:
  for +a: T.Q
  for +b: T.Q
  {T.normalize(T.Meet{T.Quantity{a},T.Quantity{b}}) ==
   T.Quantity{T.meet(a,b)} : T.Expr}


law meet_zero_left:
  for +expr: T.Expr
  {T.reduce(T.Quantity{T.QZero{}},expr) == T.Quantity{T.QZero{}} : T.Expr}

law meet_zero_right:
  for +expr: T.Expr
  {T.reduce(expr,T.Quantity{T.QZero{}}) == T.Quantity{T.QZero{}} : T.Expr}

law meet_many_left:
  for +expr: T.Expr
  {T.reduce(T.Quantity{T.QMany{}},expr) == expr : T.Expr}

law meet_many_right:
  for +expr: T.Expr
  {T.reduce(expr,T.Quantity{T.QMany{}}) == expr : T.Expr}
