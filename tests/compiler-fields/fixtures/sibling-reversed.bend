type Flag is Data:
  Off{}
  On{}
type Pair is Type:
  Pair{left: Flag, right: Flag}
def read(x: Pair) -> Flag:
  match x:
    case Pair{a,b}:
      match b:
        case Off{}:
          a
        case On{}:
          match a:
            case Off{}:
              On{}
            case On{}:
              Off{}
def main() -> Flag:
  read(Pair{On{},On{}})
