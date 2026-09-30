type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(x: Flag, y: Flag) -> Flag:
  h(x ?y)

def main() -> Flag:
  f(On{}, Off{})
