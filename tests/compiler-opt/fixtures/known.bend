type Flag is Data:
  Off{}
  On{}
def choose(x: Flag) -> Flag:
  match x:
    case On{}: On{}
    case Off{}: Off{}
def main() -> Flag:
  choose(On{})
