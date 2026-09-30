# Recursion on a list tail two cells down, under overlapping rows and a final wildcard.
type Flag is Data:
  Off{}
  On{}

type L is Type:
  Nil{}
  Cons{h: Flag, t: L}

def alt(xs: L) -> Flag:
  match xs:
    case Nil{}: On{}
    case Cons{On{}, Nil{}}: On{}
    case Cons{On{}, Cons{Off{}, rest}}: alt(rest)
    case _: Off{}

def alt3(a: Flag, b: Flag, c: Flag) -> Flag:
  alt(Cons{a, Cons{b, Cons{c, Nil{}}}})

def alt4(a: Flag, b: Flag, c: Flag, d: Flag) -> Flag:
  alt(Cons{a, Cons{b, Cons{c, Cons{d, Nil{}}}}})

def main() -> Flag:
  alt3(On{}, Off{}, On{})
