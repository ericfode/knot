# A wildcard row covers the constructors on both sides of an explicit middle row.
type Color is Data:
  Red{}
  Green{}
  Blue{}

def bump(c: Color) -> Color:
  match c:
    case Green{}: Blue{}
    case _: Green{}

def constant(c: Color) -> Color:
  match c:
    case _: Blue{}

def main() -> Color:
  bump(Red{})
