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

def use(+a: Flag) -> Flag:
  f : Flag -> Flag = x => xor(a,x)
  g : Flag -> Flag = x => keep(a,x)
  h : Flag -> Flag = x => xor(a,x)
  xor(f(Off{}),xor(g(Off{}),h(Off{})))

def main() -> Flag:
  use(On{})
