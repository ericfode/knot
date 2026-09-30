type Flag is Data:
  Off{}
  On{}

type Pr is Type:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

def f(a: Flag) -> Flag:
  match a:
    case _: On{}
    case Off{}: On{} -> Off{}

def main() -> Flag:
  f(On{})
