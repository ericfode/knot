# A named def as a ~ argument, forwarded by one template to a template declared above it.
type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def twice(~f: Flag -> Flag, x: Flag) -> Flag:
  f(f(x))

def thrice(~f: Flag -> Flag, x: Flag) -> Flag:
  twice(~f,f(x))

def flip(x: Flag) -> Flag:
  thrice(~invert,x)

def same(x: Flag) -> Flag:
  twice(~invert,x)

def main() -> Flag:
  flip(On{})
