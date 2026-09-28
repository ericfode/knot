# A partial self-call whose supplied argument does not shrink.
type Flag is Data:
  Off{}
  On{}

type Bits is Data:
  Nil{}
  Cons{head: Flag, tail: Bits}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def walk(xs: Bits, acc: Flag) -> Flag:
  match xs:
    case Nil{}: acc
    case Cons{h, t}: apply(walk(xs), xor(h, acc))

def main() -> Flag:
  walk(Cons{On{}, Nil{}}, Off{})
