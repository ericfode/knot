type Flag is Data:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def first(p: P) -> Flag:
  match p:
    case P{x, y}: x

def main() -> Flag:
  first(P{On {}, Off{}})
