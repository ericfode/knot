type Flag is Data:
  Off{}
  On{}

def ident(x: Flag) -> Flag:
  match x:
    case _: On{}

def main() -> Flag:
  ident(Off{})
