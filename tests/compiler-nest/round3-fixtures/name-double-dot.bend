type Flag is Data:
  Off{}
  On{}

def f(a..b: Flag) -> Flag:
  On{}

def main() -> Flag:
  f(On{})
