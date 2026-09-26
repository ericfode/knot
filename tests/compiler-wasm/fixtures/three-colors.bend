type Color is Type:
  Red{}
  Green{}
  Blue{}

def cycle(c: Color) -> Color:
  match c:
    case Red{}: Green{}
    case Green{}: Blue{}
    case Blue{}: Red{}

def main() -> Color:
  cycle(Green{})
