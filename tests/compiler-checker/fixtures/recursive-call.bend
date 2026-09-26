type Flag is Type:
  Off{}
  On{}
def f(x: Flag) -> Flag:
  f(x)
def main() -> Flag:
  f(On{})
