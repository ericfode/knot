type Flag is Data:
  Off{}
  On{}
def drain(+n: Flag) -> Flag:
  -unused = drain(n)
  n
def main() -> Flag:
  drain(On{})
