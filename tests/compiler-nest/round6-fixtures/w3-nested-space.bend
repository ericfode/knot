type Flag is Data:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def f(p: P) -> Flag:
  match p:
    case P{On {}, y}: y
    case P{x, y}: x

def main() -> Flag:
  f(P{On{}, Off{}})
