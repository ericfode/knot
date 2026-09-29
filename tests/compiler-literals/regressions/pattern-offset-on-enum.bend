import Base

# A Nat offset pattern names no constructor of Answer.
type Answer is Type:
  No{}
  Yes{}

def inspect(a: Answer) -> Answer:
  match a:
    case 1n+p: No{}
    case _: Yes{}

def main() -> Answer:
  inspect(Yes{})
