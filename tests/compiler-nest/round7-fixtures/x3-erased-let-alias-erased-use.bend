type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def keep(a: Flag, -b: Flag) -> Flag:
  a

def f(a: Flag, b: Flag) -> Flag:
  -k = a
  match k:
    case y: keep(b, y)
