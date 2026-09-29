import Base

# A String literal scrutinee is already a constructor value.
type Answer is Type:
  No{}
  Yes{}

def inspect() -> Answer:
  match "ab":
    case "ab": Yes{}
    case _: No{}

def main() -> Answer:
  inspect()
