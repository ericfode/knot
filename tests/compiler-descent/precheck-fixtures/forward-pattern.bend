type V is Type:

def f(x: V, y: Flag) -> Flag:
  match x y:
    case _ On{}: Off{}

def main() -> Flag:
  On{}

type Flag is Data:
  Off{}
  On{}
