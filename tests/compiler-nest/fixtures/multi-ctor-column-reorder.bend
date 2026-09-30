# A constructor column on b closes the earlier parameter a, which cannot be matched after it.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def gate(a: Flag, b: Color) -> Color:
  match b a:
    case Red{} On{}: Red{}
    case y On{}: y
    case y Off{}: Red{}

def main() -> Color:
  gate(On{}, Blue{})
