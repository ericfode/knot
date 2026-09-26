type Flag is Type:
  Off{}
  On{}
def identity(x: Flag) -> Flag:
  x
def f(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}:
      y = identity(y)
      y
    case On{}:
      y : Flag = Off{}
      y : Flag = On{}
      y
def main() -> Flag:
  f(Off{},Off{})
