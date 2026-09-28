type Flag is Data:
  Off{}
  On{}
type Pair is Data:
  Pair{left: Flag, right: Flag}

def first(+x: Flag, +y: Flag) -> Flag:
  x

def second(p: Pair) -> Flag:
  match p:
    case Pair{left,right}: right

def main() -> Flag:
  second(Pair{Off{},first(Off{},On{})})
