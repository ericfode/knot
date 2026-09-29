import Base

# A promoted binder does not supply the Nat literal a type.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  +n = 3n
  answer(Nat.is_eq(n, n))

def main() -> Answer:
  bound()
