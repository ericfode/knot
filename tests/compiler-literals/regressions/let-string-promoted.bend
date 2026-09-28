import Base

# A promoted binder does not supply the String literal a type.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  +s = "ab"
  answer(String.eq(s, s))

def main() -> Answer:
  bound()
