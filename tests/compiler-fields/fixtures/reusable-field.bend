type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{+value: Flag}
def first(a: Flag, b: Flag) -> Flag:
  a
def reuse(x: Box) -> Flag:
  match x:
    case Box{v}:
      first(v,v)
def main() -> Flag:
  reuse(Box{On{}})
