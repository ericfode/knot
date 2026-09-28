# A ~ binder after a plain binder.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def tint(f: Flag, ~c: Color) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: c

def main() -> Color:
  tint(On{},~Blue{})
