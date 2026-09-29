# A wildcard row reaching the default region uses the scrutinized parameter twice.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(x: Flag) -> Flag:
  match x:
    case On{}: On{}
    case _: both(x, x)

def main() -> Flag:
  f(Off{})
