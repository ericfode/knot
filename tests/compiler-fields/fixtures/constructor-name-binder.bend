type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def read(x: Box) -> Flag:
  match x:
    case Box{On}:
      On{}
def main() -> Flag:
  read(Box{On{}})
