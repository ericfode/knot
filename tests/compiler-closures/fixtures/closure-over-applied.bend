# f: Flag -> Flag receives two arguments; f(x) is a Flag, which cannot be applied again.
type Flag is Data:
  Off{}
  On{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x, On{})

def main() -> Flag:
  apply(y => y, On{})
