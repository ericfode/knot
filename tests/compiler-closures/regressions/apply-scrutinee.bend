type Flag is Data:
  Off{}
  On{}

def gate(k: Flag) -> Flag -> Flag:
  x => k

def main() -> Flag:
  match gate(On{})(Off{}):
    case On{}: On{}
    case Off{}: Off{}
