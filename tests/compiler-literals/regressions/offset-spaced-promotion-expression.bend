import Base

# `3n +x` separates the literal from `+`.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def five(x: Nat) -> Answer:
  answer(Nat.is_eq(3n +x, 5n))

def main() -> Answer:
  five(2n)
