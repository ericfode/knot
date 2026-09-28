# Continuation-passing folds over a user list; one self-call sits inside a continuation lambda.
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

def feed(x: Flag, next: Flag -> Flag) -> Flag:
  next(x)

def walk(xs: Bits, k: Flag -> Flag) -> Flag:
  match xs:
    case Nil{}: k(Off{})
    case Cons{h, t}: walk(t, y => k(xor(h, y)))

def nested(xs: Bits, k: Flag -> Flag) -> Flag:
  match xs:
    case Nil{}: k(Off{})
    case Cons{h, t}: feed(h, y => nested(t, z => k(xor(y, z))))

def parity(a: Flag, b: Flag, c: Flag) -> Flag:
  walk(Cons{a, Cons{b, Cons{c, Nil{}}}}, y => y)

def odd_nested(a: Flag, b: Flag, c: Flag) -> Flag:
  nested(Cons{a, Cons{b, Cons{c, Nil{}}}}, y => invert(y))

def main() -> Flag:
  parity(On{}, On{}, On{})
