type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  -a.b = x
  x

def main() -> Flag:
  f(On{})
