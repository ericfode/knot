type Flag is Data:
  Off{}
  On{}

def copy(x: Flag) -> Flag:
  match x:
    case Off{}:
      y : Flag = x
      y
    case On{}:
      y : Flag = x
      y

def main() -> Flag:
  copy(On{})
