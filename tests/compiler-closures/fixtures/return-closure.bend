# A definition returns a closure over its parameter; the closure is applied three ways.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def gate(k: Flag) -> Flag -> Flag:
  x => both(k, x)

def chained(k: Flag, x: Flag) -> Flag:
  gate(k)(x)

def bound(k: Flag, x: Flag) -> Flag:
  g = gate(k)
  g(x)

def annotated(k: Flag, x: Flag) -> Flag:
  g : Flag -> Flag = y => both(y, k)
  g(x)

def main() -> Flag:
  bound(On{}, On{})
