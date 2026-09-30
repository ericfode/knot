type Flag is Data:
  Off{}
  On{}

def f(a: Flag,
  +b: Flag) -> Flag:
  b

def main() -> Flag:
  f(Off{},On{})
