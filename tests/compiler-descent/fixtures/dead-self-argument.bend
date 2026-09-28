type Flag is Data:
  Off{}
  On{}
def keep(-ghost: Flag, x: Flag) -> Flag:
  x
def drain(+n: Flag) -> Flag:
  keep(drain(n),n)
def main() -> Flag:
  drain(On{})
