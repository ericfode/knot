type Flag is Data:
  Off{}
  On{}
type Pair is Type:
  Pair{left: Flag, right: Flag}
def read(x: Pair) -> Flag:
  match x:
    case Pair{a,b}:
      match a:
        case Off{}:
          b
        case On{}:
          match b:
            case Off{}:
              On{}
            case On{}:
              Off{}
def main() -> Flag:
  read(Pair{On{},Off{}})
