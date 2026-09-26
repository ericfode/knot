type Flag is Type:
  Off{}
  On{}
def f(x: Flag) -> Flag:
  +y = x
  y
def main() -> Flag:
  f(On{})
