type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}

def read(b: Box) -> Flag:
  match b:
    case Box{x}:
      y = x
      y

def main() -> Flag:
  read(Box{On{}})
