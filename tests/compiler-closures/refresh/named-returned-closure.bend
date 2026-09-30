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

def close(a: Flag) -> Flag -> Flag:
  x => xor(a,x)

def use(f: Flag -> Flag -> Flag) -> Flag:
  f(On{},On{})

def main() -> Flag:
  use(close)
