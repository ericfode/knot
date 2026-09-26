type Flag is Type:
  Off{}
  On{}
def first(a: Flag,b: Flag) -> Flag:
  a
def f(x: Flag,y: Flag) -> Flag:
  match x:
    case Off{}: first(y,y)
    case On{}: y
def main() -> Flag:
  f(Off{},On{})
