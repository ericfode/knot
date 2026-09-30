type Flag is Data:
  Off{}
  On{}

type Q is Data:
  Q0{}
  Q1{}
  Q2{}
  Q3{}

def pair(a: Flag, b: Flag) -> Flag:
  a

def f(a: Q, b: Q, c: Q, d: Q, e: Q, f: Q, g: Q) -> Flag:
  match a b c d e f g:
    case Q0{} _ _ _ _ _ _: pair(On{}, On{})
    case _ Q0{} _ _ _ _ _: pair(Off{}, Off{})
    case _ _ Q0{} _ _ _ _: pair(On{}, On{})
    case _ _ _ Q0{} _ _ _: pair(Off{}, Off{})
    case _ _ _ _ Q0{} _ _: pair(On{}, On{})
    case _ _ _ _ _ Q0{} _: pair(Off{}, Off{})
    case _ _ _ _ _ _ Q0{}: pair(On{}, On{})
    case _ _ _ _ _ _ _: pair(On{}, On{})

def main() -> Flag:
  f(Q1{}, Q1{}, Q1{}, Q1{}, Q1{}, Q1{}, Q1{})
