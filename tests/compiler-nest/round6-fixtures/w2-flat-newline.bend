type Flag is Data:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def f(x: Flag) -> Flag:
  match x:
    case On
      {}: Off{}
    case Off{}: On{}

def main() -> Flag:
  f(On{})
