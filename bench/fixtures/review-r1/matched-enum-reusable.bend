type Flag is Data:
  Off{}
  On{}

def copy(x: Flag) -> Flag:
  match x:
    case Off{}:
      +y = x
      y
    case On{}:
      +y = x
      y

def main() -> Flag:
  copy(On{})
