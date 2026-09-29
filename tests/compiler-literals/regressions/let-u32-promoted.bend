import Base

# A promoted binder does not supply the U32 literal a type.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  +n = 3
  answer(U32.is_eq(n, n))

def main() -> Answer:
  bound()
