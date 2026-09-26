type Flag is Type:
  Off{}
  On{}
def first(a: Flag,b: Flag) -> Flag:
  a
def f(-ghost: Flag) -> Flag:
  y = ghost
  On{}
def main() -> Flag:
  f(On{})
