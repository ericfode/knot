type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(x: Flag) -> Flag:
  match x:
    case _: On{}
    case Off{}:
      h(x ?y)

def main() -> Flag:
  f(On{})
