import Base

# A Nat offset scrutinee is already a successor constructor.
type Answer is Type:
  No{}
  Yes{}

def inspect(m: Nat) -> Answer:
  match 1n+m:
    case 3n: Yes{}
    case _: No{}

def main() -> Answer:
  inspect(2n)
