import Base

# A String literal checks against a known type; `s = "ab"` has none.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  s = "ab"
  answer(String.eq(s, "ab"))

def main() -> Answer:
  bound()
