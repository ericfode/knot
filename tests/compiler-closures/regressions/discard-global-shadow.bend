type Flag is Data:
  Off{}
  On{}

def _() -> Flag:
  On{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def main() -> Flag:
  apply(_ => _, Off{})
