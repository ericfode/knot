# One apply site receives every shape of function value, so a defunctionalized apply needs one tag per shape.
type Flag is Data:
  Off{}
  On{}

type Shape is Data:
  Bare{}
  One{}
  Two{}
  Named{}
  Partial{}
  Made{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def gate(k: Flag) -> Flag -> Flag:
  x => both(k, x)

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def site(s: Shape, +k: Flag, x: Flag) -> Flag:
  match s:
    case Bare{}: apply(y => invert(y), x)
    case One{}: apply(y => xor(k, y), x)
    case Two{}:
      m : Flag = invert(k)
      apply(y => both(m, xor(k, y)), x)
    case Named{}: apply(invert, x)
    case Partial{}: apply(xor(k), x)
    case Made{}: apply(gate(k), x)

def main() -> Flag:
  site(Two{}, Off{}, Off{})
