# The out-of-order column b holds only variables, so it binds without closing a.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def gate(a: Flag, b: Color) -> Color:
  match b a:
    case y On{}: y
    case y Off{}: Red{}

def main() -> Color:
  gate(On{}, Blue{})
