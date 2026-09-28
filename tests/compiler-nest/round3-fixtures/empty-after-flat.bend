type Flag is Data:
  Off{}
  On{}

type V is Type:

type P2 is Type:
  P2{a: Flag, b: Flag}

def f(y: Flag, x: V) -> Flag:
  match y:
    case On{}: Off{}

def main() -> Flag:
  On{}
