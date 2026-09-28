type Flag is Type:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def g(a: Flag, b: Flag) -> Flag:
  flip = a
  flip(b)
