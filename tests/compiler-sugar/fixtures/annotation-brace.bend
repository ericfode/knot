# A brace annotation {term : T} types a constructor as an argument or a let initializer.
type Flag is Data:
  Off{}
  On{}

def pick(f: Flag, g: Flag) -> Flag:
  match f:
    case On{}: g
    case Off{}: On{}

def argument(f: Flag) -> Flag:
  pick({On{} : Flag},f)

def held(f: Flag) -> Flag:
  x = {Off{} : Flag}
  pick(x,f)

def main() -> Flag:
  argument(Off{})
