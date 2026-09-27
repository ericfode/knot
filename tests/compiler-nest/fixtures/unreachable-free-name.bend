# A repeated row after full coverage names an unbound variable: the seed drops it unresolved.
type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}
    case Off{}: nope

def main() -> Flag:
  flip(Off{})
