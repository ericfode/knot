# A bare declared constructor name is not a binder: the pattern must be written On{}.
type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case On: Off{}
    case Off{}: On{}

def main() -> Flag:
  flip(Off{})
