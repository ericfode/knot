type Flag is Data:
  Off{}
  On{}

def pick(a, x: Flag) -> Flag:
  x

def main() -> Flag:
  pick(&2, On{})
