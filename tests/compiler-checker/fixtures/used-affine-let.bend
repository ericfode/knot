type Flag is Type:
  Off{}
  On{}
def first(a: Flag,b: Flag) -> Flag:
  a
def f(x: Flag) -> Flag:
  y = x
  first(y,x)
def main() -> Flag:
  f(On{})
