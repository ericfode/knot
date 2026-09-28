type Flag is Data:
  Off{}
  On{}

def round(x: Flag) -> Flag:
  match x:
    case Off{}:
      -Alias : Type = Flag
      On{}
    case On{}:
      Off{}

def main() -> Flag:
  round(Off{})
