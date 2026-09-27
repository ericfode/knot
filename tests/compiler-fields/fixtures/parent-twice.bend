type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def first(x: Box, y: Box) -> Box:
  x
def again(x: Box) -> Box:
  match x:
    case Box{v}:
      first(x,x)
def main() -> Box:
  again(Box{On{}})
