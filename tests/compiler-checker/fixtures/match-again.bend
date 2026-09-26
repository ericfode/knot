type Flag is Type:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}:
      match x:
        case Off{}: Off{}
        case On{}: On{}
    case On{}: On{}
def main() -> Flag:
  f(On{})
