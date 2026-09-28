type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  P{a..b: Flag}

def f(x: Flag) -> Flag:
  x

def main() -> Flag:
  f(On{})
