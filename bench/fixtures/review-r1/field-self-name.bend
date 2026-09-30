type Flag is Data:
  Off{}
  On{}

type Box is Type:
  Box{Flag: Flag}

def read(b: Box) -> Flag:
  match b:
    case Box{x}: x

def main() -> Flag:
  read(Box{On{}})
