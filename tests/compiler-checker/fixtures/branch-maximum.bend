type Flag is Type:
  Off{}
  On{}
def f(x: Flag,y: Flag) -> Flag:
  match x:
    case Off{}: y
    case On{}: y
def main() -> Flag:
  f(Off{},On{})
