# map applies one closure to every element, consuming f more than once (Base writes List.map as a template).
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

def map(xs: Bits, f: Flag -> Flag) -> Bits:
  match xs:
    case Nil{}: Nil{}
    case Cons{h, t}: Cons{f(h), map(t, f)}

def first(xs: Bits) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Cons{h, t}: h

def main() -> Flag:
  first(map(Cons{On{}, Nil{}}, invert))
