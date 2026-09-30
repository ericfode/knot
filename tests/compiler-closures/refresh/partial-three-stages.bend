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

def mix(a: Flag, b: Flag, c: Flag) -> Flag:
  xor(a,xor(b,c))

def main() -> Flag:
  f : Flag -> Flag -> Flag = mix(On{})
  g : Flag -> Flag = f(On{})
  g(On{})
