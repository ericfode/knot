type Flag is Data:
  Off{}
  On{}

type V is Type:

def f(x: V, y: Flag) -> Flag:
  match x y:
    case z On{}: Off{}

def main() -> Flag:
  On{}
