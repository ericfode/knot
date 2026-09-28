# map written as a template: ~f is substituted at compile time, so every element may use it (templates are S3).
type Flag is Data:
  Off{}
  On{}

type Bits is Data:
  Nil{}
  Cons{head: Flag, tail: Bits}

def map(~f: Flag -> Flag, xs: Bits) -> Bits:
  match xs:
    case Nil{}: Nil{}
    case Cons{h, t}: Cons{f(h), map(~f, t)}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def parity(xs: Bits) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Cons{h, t}: xor(h, parity(t))

def run(a: Flag, b: Flag, c: Flag) -> Flag:
  parity(map(~invert, Cons{a, Cons{b, Cons{c, Nil{}}}}))

def main() -> Flag:
  run(On{}, On{}, Off{})
