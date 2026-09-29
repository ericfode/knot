type Flag is Data:
  Off{}
  On{}

def f.g(x: Flag) -> Flag:
  x

def main() -> Flag:
  f.g(Off{})
