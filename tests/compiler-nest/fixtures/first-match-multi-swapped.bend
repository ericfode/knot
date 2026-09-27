# The rows of first-match-multi with the first two swapped: On{} On{} now reaches R2.
type Flag is Data:
  Off{}
  On{}

type Row is Data:
  R1{}
  R2{}
  R3{}

def rank(a: Flag, b: Flag) -> Row:
  match a b:
    case _ On{}: R2{}
    case On{} _: R1{}
    case _ _: R3{}

def main() -> Row:
  rank(On{}, On{})
