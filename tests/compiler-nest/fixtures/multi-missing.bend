# Two scrutinees; the pair Off{} On{} is covered by no row.
type Flag is Data:
  Off{}
  On{}

def cover(a: Flag, b: Flag) -> Flag:
  match a b:
    case On{} _: On{}
    case Off{} Off{}: Off{}

def main() -> Flag:
  cover(On{}, On{})
