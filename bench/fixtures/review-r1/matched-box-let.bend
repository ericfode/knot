type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}

def read(b: Box) -> Flag:
  match b:
    case Box{x}: x

def copy(b: Box) -> Flag:
  match b:
    case Box{x}:
      copy = b
      read(copy)

def main() -> Flag:
  copy(Box{On{}})
