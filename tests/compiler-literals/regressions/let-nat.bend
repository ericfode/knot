import Base

# A Nat literal checks against a known type; `n = 3n` has none.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  n = 3n
  answer(Nat.is_eq(n, 3n))

def main() -> Answer:
  bound()
