type Flag is Data:
  Off{}
  On{}

type P..Q is Type:
  PQ{a: Flag}

def f(x: Flag) -> Flag:
  x

def main() -> Flag:
  f(On{})
