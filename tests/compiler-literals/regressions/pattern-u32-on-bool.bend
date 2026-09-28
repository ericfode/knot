import Base

# A U32 literal pattern names no constructor of Bool.
type Answer is Type:
  No{}
  Yes{}

def inspect(a: Bool) -> Answer:
  match a:
    case 0: No{}
    case _: Yes{}

def main() -> Answer:
  inspect(True{})
