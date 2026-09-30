type Flag is Data:
  Off{}
  On{}

type Box is Data:
  Box{Flag: Flag, value: Flag}

def read(b: Box) -> Flag:
  match b:
    case Box{x,y}: y

def main() -> Flag:
  read(Box{Off{},On{}})
