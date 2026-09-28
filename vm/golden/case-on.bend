type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def main() -> Flag:
  flip(On{})
