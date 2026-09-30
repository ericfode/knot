type Flag is Data:
  Off{}
  On{}

def ident(x: Flag) -> Flag:
  match x:
    case _x: _x

def main() -> Flag:
  ident(On{})
