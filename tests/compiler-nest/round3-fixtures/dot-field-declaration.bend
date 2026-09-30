type Flag is Data:
  Off{}
  On{}

type Box is Type:
  B{a.b: Flag}

def f(p: Box) -> Flag:
  match p:
    case B{x}: x

def main() -> Flag:
  f(B{On{}})
