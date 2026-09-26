type Flag is Type:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  y : Flag = Off{}
  match x:
    case Off{}: y
    case On{}: y
def main() -> Flag:
  f(On{})
