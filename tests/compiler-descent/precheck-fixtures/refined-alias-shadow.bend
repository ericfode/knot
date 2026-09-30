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
    case v:
      +v : Flag = Off{}
      both(v, v)

def main() -> Flag:
  f(Off{})
