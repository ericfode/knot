# A lambda body matches the lambda's own binder; only parameters and fields are scrutinees.
type Flag is Data:
  Off{}
  On{}

def flip(k: Flag) -> Flag -> Flag:
  y => match y:
    case On{}: k
    case Off{}: On{}

def main() -> Flag:
  flip(Off{})(On{})
