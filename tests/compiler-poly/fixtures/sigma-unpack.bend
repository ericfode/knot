# Sigma destructuring under rigid types: unpack(-A,-B,-R, p: Both(A,B), f: A -> B -> R), used at two instances.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Dep<a, b, -A: Kind(a), -B: @-x: A -> Kind(b)> is Kind(a <&> b):
  Pack{fst: A, snd: B(fst)}

def Both(-A: Type, -B: Type) -> Type:
  Dep<&1,&1,A,_ => B>

def unpack(-A: Type, -B: Type, -R: Type, p: Both(A,B), f: A -> B -> R) -> R:
  Pack{a,b} = p
  f(a,b)

def mix(f: Flag, c: Color) -> Color:
  match f:
    case Off{}: c
    case On{}: Red{}

def both(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}: Off{}
    case On{}: y

def mixed(f: Flag, c: Color) -> Color:
  unpack(Flag,Color,Color,Pack{f,c},mix)

def joined(x: Flag, y: Flag) -> Flag:
  unpack(Flag,Flag,Flag,Pack{x,y},a => b => both(b,a))

def main() -> Color:
  mixed(Off{},Blue{})
