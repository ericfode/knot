type Flag is Type:
  Off{}
  On{}
def id(x: Flag) -> Flag:
  x
def f(id: Flag) -> Flag:
  id(On{})
def main() -> Flag:
  f(On{})
