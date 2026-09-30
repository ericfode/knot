type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}

def read(b: Box) -> Flag:
  match b:
    case Box{x}: x

def copy(b: Box) -> Flag:
  y = b
  read(y)

def main() -> Flag:
  copy(Box{On{}})
