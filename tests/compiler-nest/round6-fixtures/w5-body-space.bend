type Flag is Data:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def f(x: Flag) -> Flag:
  match x:
    case On{}: On {}
    case Off{}: Off{}

def main() -> Flag:
  f(On{})
