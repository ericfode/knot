type Flag is Data:
  Off{}
  On{}

def choose(x: Flag) -> Flag:
  match x:
    case Off{}: Off{}
    case On   {}: On{}

def main() -> Flag:
  choose(On{})
