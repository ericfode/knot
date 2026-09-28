type Flag is Data:
  Off{}
  On{}

def main() -> Flag:
  match x => On{}:
    case On{}: On{}
    case Off{}: Off{}
