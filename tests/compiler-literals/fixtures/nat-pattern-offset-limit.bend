# Negative: past 256n, n+p is Nat.add(n, p), which is not a pattern.
import Base

type Answer is Type:
  No{}
  Yes{}

def past(n: Nat) -> Answer:
  match n:
    case 257n+p: Yes{}
    case _: No{}

def main() -> Answer:
  past(300n)
