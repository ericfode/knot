# A wildcard after rows that already cover every constructor names an unbound variable.
type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case On{}: On{}
    case Off{}: Off{}
    case _: nope

def main() -> Flag:
  f(On{})
