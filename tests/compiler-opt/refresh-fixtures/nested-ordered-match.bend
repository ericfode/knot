type Flag is Data:
  Off{}
  On{}

def compare(x: Flag, y: Flag) -> Flag:
  match x:
    case On{}:
      match y:
        case Off{}: On{}
        case On{}: Off{}
    case Off{}:
      match y:
        case On{}: On{}
        case Off{}: Off{}
def main() -> Flag:
  compare(On{},Off{})
