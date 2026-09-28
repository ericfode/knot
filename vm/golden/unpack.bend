type Flag is Data:
  Off{}
  On{}

type Box is Data:
  Box{item: Flag}

def get(b: Box) -> Flag:
  match b:
    case Box{x}: x

def main() -> Flag:
  get(Box{On{}})
