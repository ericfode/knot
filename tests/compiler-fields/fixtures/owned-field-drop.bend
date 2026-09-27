type Owned is Type:
  Owned{}
type Box is Type:
  Box{value: Owned}
type Flag is Data:
  Off{}
  On{}
def drop(x: Box) -> Flag:
  match x:
    case Box{v}:
      On{}
def main() -> Flag:
  drop(Box{Owned{}})
