type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  # a.. b. c.1 _.x
  x

def main() -> Flag:
  f(On{})
