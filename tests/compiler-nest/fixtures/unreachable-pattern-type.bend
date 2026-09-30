# An unreachable row still splits its column: a pattern of the wrong type is rejected.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}

def rank(x: Flag) -> Flag:
  match x:
    case _: On{}
    case Red{}: Off{}

def main() -> Flag:
  rank(Off{})
