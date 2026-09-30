# Control: all constructor rows; the scrutinee is substituted and reused as a constructor.
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
    case Off{}: both(x, x)

def main() -> Flag:
  f(Off{})
