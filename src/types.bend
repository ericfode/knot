import Base

type Q is Data:
  QZero{}
  QOne{}
  QMany{}

type Expr is Data:
  Bound{index: U32}
  Family{index: U32}
  Apply{function: Expr, argument: Expr}
  Sort{quantity: Expr}
  QuantType{}
  Quantity{value: Q}
  Meet{left: Expr, right: Expr}

type Binding is Data:
  Binding{index: U32, value: Expr}

def quantity(q: Q) -> U32:
  match q:
    case QZero{}: 0
    case QOne{}: 1
    case QMany{}: 2

def meet(a: Q, b: Q) -> Q:
  match a:
    case QZero{}: QZero{}
    case QOne{}:
      match b:
        case QZero{}: QZero{}
        case QOne{}: QOne{}
        case QMany{}: QOne{}
    case QMany{}: b

# The first binding wins. Missing indices remain rigid.
def lookup(env: List<&2,Binding>, +index: U32) -> Expr:
  match env:
    case Nil{}: Bound{index}
    case Con{Binding{id,value},tail}:
      Bool.pick(Expr,U32.is_eq(id,index),value,lookup(tail,index))

def subst(expr: Expr, +env: List<&2,Binding>) -> Expr:
  match expr:
    case Bound{index}: lookup(env,index)
    case Family{index}: Family{index}
    case Apply{function,argument}: Apply{subst(function,env),subst(argument,env)}
    case Sort{q}: Sort{subst(q,env)}
    case QuantType{}: QuantType{}
    case Quantity{q}: Quantity{q}
    case Meet{left,right}: Meet{subst(left,env),subst(right,env)}

def compose(first: List<&2,Binding>, +second: List<&2,Binding>) -> List<&2,Binding>:
  match first:
    case Nil{}: second
    case Con{Binding{index,value},tail}:
      Con{Binding{index,subst(value,second)},compose(tail,second)}

def equal(a: Expr, b: Expr) -> Bool:
  match a b:
    case Bound{i} Bound{j}: U32.is_eq(i,j)
    case Family{i} Family{j}: U32.is_eq(i,j)
    case Apply{f,x} Apply{g,y}: Bool.and(equal(f,g),equal(x,y))
    case Sort{q} Sort{r}: equal(q,r)
    case QuantType{} QuantType{}: True{}
    case Quantity{q} Quantity{r}: U32.is_eq(quantity(q),quantity(r))
    case Meet{a,b} Meet{c,d}: Bool.and(equal(a,c),equal(b,d))
    case _ _: False{}

def reduce(+left: Expr, +right: Expr) -> Expr:
  match left right:
    case Quantity{q} Quantity{r}: Quantity{meet(q,r)}
    case Quantity{QZero{}} _: Quantity{QZero{}}
    case _ Quantity{QZero{}}: Quantity{QZero{}}
    case Quantity{QMany{}} _: right
    case _ Quantity{QMany{}}: left
    case _ _: Meet{left,right}

def normalize(expr: Expr) -> Expr:
  match expr:
    case Bound{index}: Bound{index}
    case Family{index}: Family{index}
    case Apply{function,argument}: Apply{normalize(function),normalize(argument)}
    case Sort{q}: Sort{normalize(q)}
    case QuantType{}: QuantType{}
    case Quantity{q}: Quantity{q}
    case Meet{left,right}: reduce(normalize(left),normalize(right))
