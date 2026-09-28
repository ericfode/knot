# A wildcard after rows that already cover every constructor returns the wrong type.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}

def f(x: Flag) -> Flag:
  match x:
    case On{}: On{}
    case Off{}: Off{}
    case _: Red{}

def main() -> Flag:
  f(On{})
