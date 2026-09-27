type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def choose(x: Box, y: Flag) -> Flag:
  match x:
    case Box{v}:
      match v:
        case Off{}:
          y
        case On{}:
          y
def main() -> Flag:
  choose(Box{Off{}},On{})
