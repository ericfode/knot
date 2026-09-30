type Flag is Data:
  Off{}
  On{}

type L is Data:
  Nil{}
  Cons{h: Flag, t: L}

def count(xs: L) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Cons{_, Cons{On{}, _}}: On{}
    case Cons{_, t}: count(t)

def e(+a: Flag, b: Flag, c: Flag) -> Flag:
  count(Cons{a, Cons{b, Cons{c, Nil{}}}})

def main() -> Flag:
  e(Off{}, Off{}, On{})
