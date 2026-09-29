type Flag is Data:
  Off{}
  On{}

type Pr is Type:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case _ _: On{}
    case Off{} Off{}: h(On{} -> Off{})

def main() -> Flag:
  f(On{}, On{})
