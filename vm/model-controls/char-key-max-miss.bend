import Base

type Flag is Data:
  Off{}
  On{}

def top(c: Char) -> Flag:
  match c:
    case Chr{4294967295}: On{}
    case _: Off{}

def main() -> Flag:
  top(Chr{4294967294})
