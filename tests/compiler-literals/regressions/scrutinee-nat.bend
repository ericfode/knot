import Base

# A Nat literal scrutinee is already a constructor value.
type Answer is Type:
  No{}
  Yes{}

def inspect() -> Answer:
  match 3n:
    case 3n: Yes{}
    case _: No{}

def main() -> Answer:
  inspect()
