type Flag is Data:
  Off{}
  On{}

type V is Type:

type P2 is Type:
  P2{a: Flag, b: Flag}

def f(-x: V, y: Flag) -> Flag:
  match x y:
    case z On{}: Off{}

def main() -> Flag:
  On{}
