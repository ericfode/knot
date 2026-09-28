type Flag is Data:
  Off{}
  On{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def main() -> Flag:
  apply(x => x,On{})
