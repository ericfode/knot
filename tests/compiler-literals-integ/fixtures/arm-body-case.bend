# An arm body never starts with `case`: the next `case` in the arm's own column is an orphan
# case, not the body of the arm above it.
type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}:
    case On{}: Off{}

def main() -> Flag:
  f(On{})
