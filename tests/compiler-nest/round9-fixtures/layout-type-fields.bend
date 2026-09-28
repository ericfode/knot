type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  P{l: Flag,
    r: Flag}

def f(a: Flag) -> Flag:
  a

def main() -> Flag:
  f(On{})
