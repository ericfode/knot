type Flag is Data:
  Off{}
  On{}

def copy(x: Flag) -> Flag:
  match x:
    case Off{}:
      -y = x
      x
    case On{}:
      -y = x
      x

def main() -> Flag:
  copy(On{})
