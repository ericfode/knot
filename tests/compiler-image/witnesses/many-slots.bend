type Flag is Data:
  Off{}
  On{}

type List3 is Data:
  Nil3{}
  Cons3{a: Flag, b: Flag, c: Flag}

def head(xs: List3) -> Flag:
  match xs:
    case Nil3{}: Off{}
    case Cons3{a,b,c}:
      y : Flag = c
      z : Flag = b
      a

def main() -> Flag:
  head(Cons3{On{},Off{},On{}})
