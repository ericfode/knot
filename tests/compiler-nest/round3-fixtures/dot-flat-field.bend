type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  P{a: Flag, c: Flag}

def f(p: Pair) -> Flag:
  match p:
    case P{a.b, c}: a.b

def main() -> Flag:
  f(P{On{}, Off{}})
