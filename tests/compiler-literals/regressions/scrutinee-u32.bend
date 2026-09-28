import Base

# A literal scrutinee is already a constructor value.
type Answer is Type:
  No{}
  Yes{}

def inspect() -> Answer:
  match 3:
    case 3: Yes{}
    case _: No{}

def main() -> Answer:
  inspect()
