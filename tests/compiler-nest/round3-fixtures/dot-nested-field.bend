type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  P{a: Flag, c: Flag}

def f(p: Pair) -> Flag:
  match p:
    case P{a.b, On{}}: a.b
    case _: Off{}

def main() -> Flag:
  f(P{On{}, On{}})
