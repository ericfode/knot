# An unreachable row whose body has the wrong type: the seed drops it before checking.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}

def rank(x: Flag) -> Flag:
  match x:
    case _: On{}
    case On{}: Red{}

def main() -> Flag:
  rank(Off{})
