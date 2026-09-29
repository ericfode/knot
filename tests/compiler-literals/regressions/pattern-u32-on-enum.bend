import Base

# A U32 literal pattern names no constructor of Answer.
type Answer is Type:
  No{}
  Yes{}

def inspect(a: Answer) -> Answer:
  match a:
    case 3: No{}
    case _: Yes{}

def main() -> Answer:
  inspect(Yes{})
