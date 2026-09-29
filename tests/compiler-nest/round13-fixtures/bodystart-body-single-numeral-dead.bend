type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(a: Flag) -> Flag:
  match a:
    case x: x
    case On{}:
    0n

def main() -> Flag:
  f(On{})
