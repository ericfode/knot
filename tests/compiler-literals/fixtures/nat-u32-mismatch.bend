# Negative: a bare numeral is U32, never Nat (control: nat-arithmetic).
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(Nat.is_eq(Nat.add(5, 1n), 6n))
