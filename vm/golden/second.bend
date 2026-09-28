type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  Pair{left: Flag, right: Flag}

def second(p: Pair) -> Flag:
  match p:
    case Pair{a,b}: b

def main() -> Flag:
  second(Pair{Off{},On{}})
