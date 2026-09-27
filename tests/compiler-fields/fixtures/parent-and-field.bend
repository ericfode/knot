type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def first(v: Flag, x: Box) -> Flag:
  v
def reuse(x: Box) -> Flag:
  match x:
    case Box{v}:
      first(v,x)
def main() -> Flag:
  reuse(Box{On{}})
