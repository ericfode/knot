type Flag is Data:
  Off{}
  On{}

type Pr is Type:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

def Pair(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: On{}
    case Off{}: b

def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case Off{} Off{}: a & a
    case _ _: On{}

def main() -> Flag:
  f(On{}, On{})
