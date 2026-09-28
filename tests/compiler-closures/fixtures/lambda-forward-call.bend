# A lambda body calls a definition declared below it.
type Flag is Data:
  Off{}
  On{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def by_lambda(x: Flag) -> Flag:
  apply(y => later(y), x)

def later(x: Flag) -> Flag:
  x

def main() -> Flag:
  by_lambda(On{})
