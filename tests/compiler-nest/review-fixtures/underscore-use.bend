type Flag is Data:
  Off{}
  On{}

def ident(x: Flag) -> Flag:
  match x:
    case _: _

def main() -> Flag:
  ident(On{})
