type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def open(x: Box) -> Flag:
  match x:
    case Box{v}:
      v
def main() -> Flag:
  open(Box{On{}})
