type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(a: Flag, b: Flag) -> Flag:
  match a:
    case y: both(y, y)
