import Base

type Flag is Data:
  Off{}
  On{}

def pick(c: Char) -> Flag:
  match c:
    case Chr{n}: On{}

def main() -> Flag:
  pick('A')
