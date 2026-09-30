# Knot-specific: a match arm applies a function-typed parameter, outside this stage.
type Flag is Data:
  Off{}
  On{}

def apply(x: Flag, f: Flag -> Flag) -> Flag:
  match x:
    case On{}: f(Off{})
    case Off{}: Off{}

def flipped(x: Flag) -> Flag:
  apply(x, \{On: Off{}; Off: On{}})

def main() -> Flag:
  flipped(On{})
