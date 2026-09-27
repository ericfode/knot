# Two scrutinees of different types; one row per pair, in scrambled order.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def mix(f: Flag, c: Color) -> Color:
  match f c:
    case On{} Blue{}: Green{}
    case Off{} Green{}: Blue{}
    case On{} Red{}: Blue{}
    case Off{} Blue{}: Red{}
    case On{} Green{}: Red{}
    case Off{} Red{}: Green{}

def main() -> Color:
  mix(On{}, Green{})
