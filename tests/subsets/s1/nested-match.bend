type Flag is Type:
  Off{}
  On{}

def both(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}:
      match y:
        case Off{}: On{}
        case On{}: Off{}
    case On{}: y

def main() -> Flag:
  both(Off{},Off{})
