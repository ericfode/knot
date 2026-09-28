type Flag is Type:
  Off{}
  On{}

type Mark is Type:
  Unit0{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case Mark: Mark

type Other is Type:
  Mark{}

