# Without a + mark, a variable pattern keeps the parameter affine: two uses are rejected.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def square(x: Flag) -> Flag:
  match x:
    case v: both(v, v)

def main() -> Flag:
  square(On{})
