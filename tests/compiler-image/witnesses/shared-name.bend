type Pair is Data:
  Pair{first: Flag, second: Flag}

type Flag is Data:
  Off{}
  On{}

def swap(p: Pair) -> Pair:
  match p:
    case Pair{a,b}: Pair{b,a}

def main() -> Pair:
  swap(Pair{Off{},On{}})
