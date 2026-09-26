type Flag is Type:
  Off{}
  On{}
def first(a: Flag, -ghost: Flag, b: Flag) -> Flag:
  a
def second(a: Flag, -ghost: Flag, b: Flag) -> Flag:
  b
def main() -> Flag:
  second(On{},Off{},Off{})
