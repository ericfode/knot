type Flag is Type:
  Off{}
  On{}

def f(x: Flag, y: Flag) -> Flag:
  match y:
    case Off{}:
      match x:
        case Off{}: Off{}
        case On{}: On{}
    case On{}: x
def main() -> Flag:
  f(Off{},On{})
