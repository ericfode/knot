# An arm body never starts with `def` either: a keyword heads no term.
type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}:
def g(x: Flag) -> Flag:
  x

def main() -> Flag:
  f(On{})
