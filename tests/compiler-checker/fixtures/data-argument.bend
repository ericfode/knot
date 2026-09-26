type Flag is Data:
  Off{}
  On{}

def twice(+x: Flag) -> Flag:
  x
def f(x: Flag) -> Flag:
  twice(x)
def main() -> Flag:
  f(On{})
