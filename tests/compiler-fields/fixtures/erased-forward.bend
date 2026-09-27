type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{-ghost: Flag, value: Flag}
def open(x: Box) -> Flag:
  match x:
    case Box{g,v}:
      v
def main() -> Flag:
  open(Box{later(),On{}})
def later() -> Flag:
  Off{}
