type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def read(x: Box) -> Flag:
  match x:
    case Box{v}:
      y : Flag = On{}
      match v:
        case Off{}:
          y
        case On{}:
          y
def main() -> Flag:
  read(Box{On{}})
