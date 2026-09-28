import Base
import ./types.bend as T
import ./types-LAWS.bend as L

def L.meet_associative(a,b,c):
  match a:
    case T.QZero{}: {==}
    case T.QOne{}:
      match b:
        case T.QZero{}: {==}
        case T.QOne{}:
          match c:
            case T.QZero{}: {==}
            case T.QOne{}: {==}
            case T.QMany{}: {==}
        case T.QMany{}: {==}
    case T.QMany{}: {==}

def L.meet_commutative(a,b):
  match a:
    case T.QZero{}:
      match b:
        case T.QZero{}: {==}
        case T.QOne{}: {==}
        case T.QMany{}: {==}
    case T.QOne{}:
      match b:
        case T.QZero{}: {==}
        case T.QOne{}: {==}
        case T.QMany{}: {==}
    case T.QMany{}:
      match b:
        case T.QZero{}: {==}
        case T.QOne{}: {==}
        case T.QMany{}: {==}

def L.meet_idempotent(a):
  match a:
    case T.QZero{}: {==}
    case T.QOne{}: {==}
    case T.QMany{}: {==}

def L.substitution_choice(condition,a,b,env):
  match condition:
    case False{}: {==}
    case True{}: {==}

def L.lookup_composes(first,second,index):
  match first:
    case Nil{}: {==}
    case Con{T.Binding{+id,+value},+tail}:
      Equal.trans(T.Expr,
        T.lookup(T.compose(Con{T.Binding{id,value},tail},second),index),
        Bool.pick(T.Expr,U32.is_eq(id,index),T.subst(value,second),T.subst(T.lookup(tail,index),second)),
        T.subst(T.lookup(Con{T.Binding{id,value},tail},index),second),
        Equal.cong(T.Expr,T.Expr,
          x => Bool.pick(T.Expr,U32.is_eq(id,index),T.subst(value,second),x),
          T.lookup(T.compose(tail,second),index),T.subst(T.lookup(tail,index),second),
          L.lookup_composes(tail,second,index)),
        Equal.sym(T.Expr,
          T.subst(Bool.pick(T.Expr,U32.is_eq(id,index),value,T.lookup(tail,index)),second),
          Bool.pick(T.Expr,U32.is_eq(id,index),T.subst(value,second),T.subst(T.lookup(tail,index),second)),
          L.substitution_choice(U32.is_eq(id,index),value,T.lookup(tail,index),second)))

def L.substitution_composes(expr,first,second):
  match expr:
    case T.Bound{+index}:
      Equal.sym(T.Expr,T.lookup(T.compose(first,second),index),T.subst(T.lookup(first,index),second),L.lookup_composes(first,second,index))
    case T.Family{index}: {==}
    case T.Apply{+function,+argument}:
      %L.substitution_composes(function,first,second) :
        {T.Apply{T.subst(T.subst(function,first),second),T.subst(T.subst(argument,first),second)} == T.Apply{_,T.subst(argument,T.compose(first,second))} : T.Expr}
      %L.substitution_composes(argument,first,second) :
        {T.Apply{T.subst(T.subst(function,first),second),T.subst(T.subst(argument,first),second)} == T.Apply{T.subst(T.subst(function,first),second),_} : T.Expr}
      {==}
    case T.Sort{+q}:
      Equal.cong(T.Expr,T.Expr,x => T.Sort{x},T.subst(T.subst(q,first),second),T.subst(q,T.compose(first,second)),L.substitution_composes(q,first,second))
    case T.QuantType{}: {==}
    case T.Quantity{q}: {==}
    case T.Meet{+left,+right}:
      %L.substitution_composes(left,first,second) :
        {T.Meet{T.subst(T.subst(left,first),second),T.subst(T.subst(right,first),second)} == T.Meet{_,T.subst(right,T.compose(first,second))} : T.Expr}
      %L.substitution_composes(right,first,second) :
        {T.Meet{T.subst(T.subst(left,first),second),T.subst(T.subst(right,first),second)} == T.Meet{T.subst(T.subst(left,first),second),_} : T.Expr}
      {==}

def L.substitution_identity(expr):
  match expr:
    case T.Bound{index}: {==}
    case T.Family{index}: {==}
    case T.Apply{+function,+argument}:
      %L.substitution_identity(function) : {T.Apply{T.subst(function,Nil{}),T.subst(argument,Nil{})} == T.Apply{_,argument} : T.Expr}
      %L.substitution_identity(argument) : {T.Apply{T.subst(function,Nil{}),T.subst(argument,Nil{})} == T.Apply{T.subst(function,Nil{}),_} : T.Expr}
      {==}
    case T.Sort{+q}:
      Equal.cong(T.Expr,T.Expr,x => T.Sort{x},T.subst(q,Nil{}),q,L.substitution_identity(q))
    case T.QuantType{}: {==}
    case T.Quantity{q}: {==}
    case T.Meet{+left,+right}:
      %L.substitution_identity(left) : {T.Meet{T.subst(left,Nil{}),T.subst(right,Nil{})} == T.Meet{_,right} : T.Expr}
      %L.substitution_identity(right) : {T.Meet{T.subst(left,Nil{}),T.subst(right,Nil{})} == T.Meet{T.subst(left,Nil{}),_} : T.Expr}
      {==}

def L.literal_meet_normalizes(a,b):
  match a b:
    case T.QZero{} T.QZero{}: {==}
    case T.QZero{} T.QOne{}: {==}
    case T.QZero{} T.QMany{}: {==}
    case T.QOne{} T.QZero{}: {==}
    case T.QOne{} T.QOne{}: {==}
    case T.QOne{} T.QMany{}: {==}
    case T.QMany{} T.QZero{}: {==}
    case T.QMany{} T.QOne{}: {==}
    case T.QMany{} T.QMany{}: {==}

def L.meet_zero_left(expr):
  match expr:
    case T.Bound{index}: {==}
    case T.Family{index}: {==}
    case T.Apply{function,argument}: {==}
    case T.Sort{q}: {==}
    case T.QuantType{}: {==}
    case T.Quantity{T.QZero{}}: {==}
    case T.Quantity{T.QOne{}}: {==}
    case T.Quantity{T.QMany{}}: {==}
    case T.Meet{left,right}: {==}

def L.meet_zero_right(expr):
  match expr:
    case T.Bound{index}: {==}
    case T.Family{index}: {==}
    case T.Apply{function,argument}: {==}
    case T.Sort{q}: {==}
    case T.QuantType{}: {==}
    case T.Quantity{T.QZero{}}: {==}
    case T.Quantity{T.QOne{}}: {==}
    case T.Quantity{T.QMany{}}: {==}
    case T.Meet{left,right}: {==}

def L.meet_many_left(expr):
  match expr:
    case T.Bound{index}: {==}
    case T.Family{index}: {==}
    case T.Apply{function,argument}: {==}
    case T.Sort{q}: {==}
    case T.QuantType{}: {==}
    case T.Quantity{T.QZero{}}: {==}
    case T.Quantity{T.QOne{}}: {==}
    case T.Quantity{T.QMany{}}: {==}
    case T.Meet{left,right}: {==}

def L.meet_many_right(expr):
  match expr:
    case T.Bound{index}: {==}
    case T.Family{index}: {==}
    case T.Apply{function,argument}: {==}
    case T.Sort{q}: {==}
    case T.QuantType{}: {==}
    case T.Quantity{T.QZero{}}: {==}
    case T.Quantity{T.QOne{}}: {==}
    case T.Quantity{T.QMany{}}: {==}
    case T.Meet{left,right}: {==}
