# Negative: 4294967296n exceeds the Nat literal bound (4294967295n).
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(Nat.is_eq(4294967296n, 0n))
