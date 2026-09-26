type Flag is Type:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def shadow(x: Flag) -> Flag:
  x = flip(x)
  x : Flag = On{}
  x

def main() -> Flag:
  shadow(On{})
