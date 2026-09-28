# compose captures two closures and returns a third; compositions nest.
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

def compose(f: Flag -> Flag, g: Flag -> Flag) -> Flag -> Flag:
  x => g(f(x))

def named(x: Flag) -> Flag:
  compose(invert, compose(invert, invert))(x)

def mixed(k: Flag, x: Flag) -> Flag:
  compose(y => xor(k, y), invert)(x)

def main() -> Flag:
  named(On{})
