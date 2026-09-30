type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  x.

def main() -> Flag:
  f(On{})
