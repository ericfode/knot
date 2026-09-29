import Base

# A space before `+` makes `1n + p` operator sugar, not an offset pattern.
type Answer is Type:
  No{}
  Yes{}

def positive(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n + p: Yes{}

def main() -> Answer:
  positive(3n)
