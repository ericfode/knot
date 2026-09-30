# A variable row reaching the default region uses its alias twice.
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
    case v: both(v, v)

def main() -> Flag:
  f(Off{})
