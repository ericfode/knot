import Base

# A U32 literal checks against a known type; `n = 3` has none.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  n = 3
  answer(U32.is_eq(n, 3))

def main() -> Answer:
  bound()
