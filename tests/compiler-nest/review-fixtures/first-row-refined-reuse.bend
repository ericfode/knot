# The first row uses a variable twice; a later constructor row makes the column strict.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(x: Flag) -> Flag:
  match x:
    case v: both(v, v)
    case Off{}: Off{}

def main() -> Flag:
  f(On{})
