# A ~ argument names a local variable of the caller.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def tint(~c: Color, f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: c

def run(f: Flag, d: Color) -> Color:
  tint(~d,f)

def main() -> Color:
  run(On{},Blue{})
