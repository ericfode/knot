type Flag is Type:
  Off{}
  On{}

def first(a: Flag, b: Flag) -> Flag:
  a

def reuse(x: Flag) -> Flag:
  first(x,x)

def main() -> Flag:
  reuse(On{})
