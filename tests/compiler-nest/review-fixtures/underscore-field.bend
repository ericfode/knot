type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  P{l: Flag, r: Flag}

def left(p: Pair) -> Flag:
  match p:
    case P{_, r}: _

def main() -> Flag:
  left(P{On{}, Off{}})
