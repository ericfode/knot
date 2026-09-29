# A datatype with no constructors is covered by a match with no rows.
type Flag is Data:
  Off{}
  On{}

type Never is Type:

def absurd(x: Never) -> Flag:
  match x:

def main() -> Flag:
  On{}
