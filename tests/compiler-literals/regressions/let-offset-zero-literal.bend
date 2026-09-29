import Base

# `0n+3n` reads as `3n`, which still needs a known type.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  n = 0n+3n
  answer(Nat.is_eq(n, 3n))

def main() -> Answer:
  bound()
