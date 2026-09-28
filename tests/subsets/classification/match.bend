type Flag is Type:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a b:
    case Off{} Off{}: On{}
    case Off{} On{}: Off{}
    case On{} Off{}: Off{}
    case On{} On{}: On{}

def main() -> Flag:
  both(Off{},Off{})
