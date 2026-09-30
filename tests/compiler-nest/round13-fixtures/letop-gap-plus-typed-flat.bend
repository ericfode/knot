type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(x: Flag, y: Flag) -> Flag:
  v = x
  + u : Flag = y
  u

def main() -> Flag:
  f(On{}, Off{})
