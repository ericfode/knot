type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  P{l: Flag, r: Flag}

def right(p: Pair) -> Flag:
  match p:
    case P{_, r}: r

def main() -> Flag:
  right(P{On{}, Off{}})
