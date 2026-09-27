type Flag is Data:
  Off{}
  On{}
type Pair is Type:
  Pair{left: Flag, right: Flag}
def second(x: Pair) -> Flag:
  match x:
    case Pair{v,v}:
      v
def main() -> Flag:
  second(Pair{Off{},On{}})
