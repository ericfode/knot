type Flag is Data:
  Off{}
  On{}
type Pair is Data:
  Pair{left: Flag, right: Flag}
def second(p: Pair) -> Flag:
  match p:
    case Pair{left,right}: right
def observe(x: Flag, y: Flag) -> Flag:
  second(Pair{x,y})
def main() -> Flag:
  observe(Off{},On{})
