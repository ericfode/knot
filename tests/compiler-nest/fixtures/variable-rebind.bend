# A variable pattern names the scrutinee itself; the affine value is returned once.
type Color is Type:
  Red{}
  Green{}
  Blue{}

def cap(c: Color) -> Color:
  match c:
    case Blue{}: Red{}
    case other: other

def main() -> Color:
  cap(Green{})
