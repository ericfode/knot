type Flag is Data:
  Off{}
  On{}

def negate(x: Flag) -> Flag:
  match x:
    case On{}: Off{}
    case Off{}: On{}

def main() -> Flag:
  negate(On{})
