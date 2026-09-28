# Closures that capture generic values: konst keeps an A, flip keeps an A -> B -> C, both at data and arrow instances.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def konst(-A: Type, -B: Type, x: A) -> B -> A:
  y => x

def flip(-A: Type, -B: Type, -C: Type, f: A -> B -> C) -> B -> A -> C:
  b => a => f(a,b)

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def mix(f: Flag, c: Color) -> Color:
  match f:
    case Off{}: c
    case On{}: Red{}

def kept(c: Color, f: Flag) -> Color:
  konst(Color,Flag,c)(f)

def kept_arrow(x: Flag, c: Color) -> Flag:
  konst(Flag -> Flag,Color,invert)(c)(x)

def flipped(c: Color, f: Flag) -> Color:
  flip(Flag,Color,Color,mix)(c)(f)

def main() -> Color:
  flipped(Blue{},Off{})
