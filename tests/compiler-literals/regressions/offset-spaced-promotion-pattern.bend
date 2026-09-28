import Base

# `1n +p` separates the literal from `+`; the seed does not read an offset.
type Answer is Type:
  No{}
  Yes{}

def positive(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n +p: Yes{}

def main() -> Answer:
  positive(3n)
