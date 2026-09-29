import Base

# A Char literal scrutinee is already a constructor value.
type Answer is Type:
  No{}
  Yes{}

def inspect() -> Answer:
  match 'a':
    case 'a': Yes{}
    case _: No{}

def main() -> Answer:
  inspect()
