type Flag is Type:
  Off{}
  On{}
def flip(x: Flag) -> Flag:
  match x:
    case On{}: Off{}
    case Off{}: On{}
def main() -> Flag:
  flip(Off{})
