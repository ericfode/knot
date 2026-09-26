type Flag is Data:
  Off{}
  On{}
def first(a: Flag,b: Flag) -> Flag:
  a
def f(x: Flag) -> Flag:
  first(x,x)
def main() -> Flag:
  f(On{})
