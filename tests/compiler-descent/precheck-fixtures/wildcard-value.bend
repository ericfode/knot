# The wildcard name used as a value.
type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case _: _

def main() -> Flag:
  f(On{})
