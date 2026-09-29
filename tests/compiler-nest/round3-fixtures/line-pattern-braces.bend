type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

def f(p: Pair) -> Flag:
  match p:
    case Pair{On{},
      Off{}}: On{}
    case _: Off{}

def main() -> Flag:
  f(Pair{On{}, Off{}})
