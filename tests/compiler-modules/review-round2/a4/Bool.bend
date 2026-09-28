type Flag is Type:
  Off{}
  On{}

def not(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}
