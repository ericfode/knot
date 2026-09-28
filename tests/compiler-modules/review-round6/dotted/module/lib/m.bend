type Flag is Type:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def g(x: Flag) -> Flag:
  a.b = x
  a.b
