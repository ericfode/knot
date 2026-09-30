type Flag is Data:
  Off{}
  On{}

def f(+x: Flag) -> Flag:
  +a.b = x
  a.b

def main() -> Flag:
  f(On{})
