# A template parameter: seed-valid, but templates belong to a later stage.
type Flag is Data:
  Off{}
  On{}

def twice(~f: Flag -> Flag, x: Flag) -> Flag:
  f(f(x))

def invert(x: Flag) -> Flag:
  match x:
    case Off{}:
      On{}
    case On{}:
      Off{}

def run(x: Flag) -> Flag:
  twice(~invert, x)

def main() -> Flag:
  run(On{})
