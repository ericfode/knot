type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def order(x: Box, y: Flag) -> Flag:
  match x:
    case Box{v}:
      match v:
        case Off{}:
          y
        case On{}:
          match y:
            case Off{}:
              On{}
            case On{}:
              Off{}
def main() -> Flag:
  order(Box{On{}},On{})
