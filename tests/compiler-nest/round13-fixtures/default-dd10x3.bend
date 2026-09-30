type Flag is Data:
  Off{}
  On{}

type Q is Data:
  Q0{}
  Q1{}
  Q2{}

def f(a: Q, b: Q, c: Q, d: Q, e: Q, f: Q, g: Q, h: Q, i: Q, j: Q) -> Flag:
  match a b c d e f g h i j:
    case Q0{} _ _ _ _ _ _ _ _ _: On{}
    case _ Q0{} _ _ _ _ _ _ _ _: Off{}
    case _ _ Q0{} _ _ _ _ _ _ _: On{}
    case _ _ _ Q0{} _ _ _ _ _ _: Off{}
    case _ _ _ _ Q0{} _ _ _ _ _: On{}
    case _ _ _ _ _ Q0{} _ _ _ _: Off{}
    case _ _ _ _ _ _ Q0{} _ _ _: On{}
    case _ _ _ _ _ _ _ Q0{} _ _: Off{}
    case _ _ _ _ _ _ _ _ Q0{} _: On{}
    case _ _ _ _ _ _ _ _ _ Q0{}: Off{}
    case _ _ _ _ _ _ _ _ _ _: On{}

def main() -> Flag:
  f(Q1{}, Q1{}, Q1{}, Q1{}, Q1{}, Q1{}, Q1{}, Q1{}, Q1{}, Q1{})
