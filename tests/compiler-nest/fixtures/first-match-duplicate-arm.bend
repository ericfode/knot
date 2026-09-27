# A repeated constructor row is accepted; the earlier one wins.
type Flag is Data:
  Off{}
  On{}

type Row is Data:
  R1{}
  R2{}
  R3{}

def rank(x: Flag) -> Row:
  match x:
    case On{}: R1{}
    case Off{}: R2{}
    case On{}: R3{}

def main() -> Row:
  rank(On{})
