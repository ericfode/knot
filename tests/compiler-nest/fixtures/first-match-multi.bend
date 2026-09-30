# Overlapping rows over two scrutinees: the first matching row wins.
type Flag is Data:
  Off{}
  On{}

type Row is Data:
  R1{}
  R2{}
  R3{}

def rank(a: Flag, b: Flag) -> Row:
  match a b:
    case On{} _: R1{}
    case _ On{}: R2{}
    case _ _: R3{}

def main() -> Row:
  rank(On{}, On{})
