type Flag is Data:
  Off{}
  On{}
type Pair is Type:
  Pair{left: Flag, right: Flag}
def again(x: Pair) -> Pair:
  match x:
    case Pair{v,w}:
      match v:
        case Off{}:
          v : Flag = On{}
          x
        case On{}:
          v : Flag = Off{}
          x
def main() -> Pair:
  again(Pair{Off{},On{}})
