type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def again(x: Box) -> Box:
  match x:
    case Box{v}:
      match v:
        case Off{}:
          x
        case On{}:
          x
def main() -> Box:
  again(Box{On{}})
