import Base

# `\q` is no escape, and a following `{` does not make it one.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  answer(Nat.is_eq(String.length("\q{"), 2n))
