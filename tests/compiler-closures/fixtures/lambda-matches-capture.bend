# A lambda body matches a captured definition parameter; the seed rejects the match.
type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def pick(x: Flag) -> Flag -> Flag:
  y => match x:
    case On{}: y
    case Off{}: invert(y)

def main() -> Flag:
  pick(Off{})(On{})
