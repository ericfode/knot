type Flag is Type:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}

def main() -> Flag:
  flip(Off{})
