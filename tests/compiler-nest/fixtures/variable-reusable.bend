# A + mark on a variable pattern makes the matched Data parameter reusable.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def square(x: Flag) -> Flag:
  match x:
    case +v: both(v, v)

def main() -> Flag:
  square(On{})
