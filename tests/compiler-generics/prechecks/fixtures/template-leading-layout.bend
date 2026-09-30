type Flag is Data:
  Off{}
  On{}

def f(
  ~b: Flag,
  a: Flag) -> Flag:
  a

def main() -> Flag:
  On{}
