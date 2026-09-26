type Flag is Type:
  Off{}
  On{}

def first(a: Flag, b: Flag) -> Flag:
  a
def f(x: Flag) -> Flag:
  match x:
    case Off{}: first(x,x)
    case On{}: first(x,x)
def main() -> Flag:
  f(On{})
