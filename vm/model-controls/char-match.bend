import Base

def code(c: Char) -> U32:
  match c:
    case Chr{n}: 7

def main() -> Bool:
  U32.is_eq(code('A'),7)
