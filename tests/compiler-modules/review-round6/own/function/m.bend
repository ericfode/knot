type Flag is Type:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  x

def m.f(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}
