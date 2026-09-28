type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case On{ }: Off{}
    case Off{}: On{}

def main() -> Flag:
  f(On{})
