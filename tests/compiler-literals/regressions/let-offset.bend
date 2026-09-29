import Base

# A Nat offset is a successor constructor; `n = 2n+m` has no known type.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound(m: Nat) -> Answer:
  n = 2n+m
  answer(Nat.is_eq(n, 4n))

def main() -> Answer:
  bound(2n)
