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

type Color is Data:
  Red{}
  Blue{}

def color(x: Color) -> Flag:
  match x:
    case Red{}: Off{}
    case Blue{}: On{}

def use(a: Flag, c: Color) -> Flag:
  f : Flag -> Flag = x => xor(a,x)
  g : Color -> Flag = x => color(x)
  xor(f(Off{}),g(c))

def main() -> Flag:
  use(Off{},Blue{})
