type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def keep(a: Flag, b: Flag) -> Flag:
  a

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def with_function(f: (Flag -> Flag) -> Flag, g: Flag -> Flag) -> Flag:
  f(g)

def shadow(invert: Flag -> Flag) -> Flag:
  with_function(invert => invert(On{}), invert)

def main() -> Flag:
  shadow(invert)
