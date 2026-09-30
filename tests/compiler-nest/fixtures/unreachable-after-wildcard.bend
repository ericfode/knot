# A well-typed row after a wildcard is unreachable; every input takes the wildcard row.
type Flag is Data:
  Off{}
  On{}

type Row is Data:
  R1{}
  R2{}

def rank(x: Flag) -> Row:
  match x:
    case _: R1{}
    case On{}: R2{}

def main() -> Row:
  rank(On{})
