type Flag is Data:
  Off{}
  On{}

def f(a: Flag,
      b: Flag) -> Flag:
  a

def main() -> Flag:
  f(On{}, Off{})
