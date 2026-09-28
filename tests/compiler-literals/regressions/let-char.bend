import Base

# A Char literal checks against a known type; `c = 'a'` has none.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def bound() -> Answer:
  c = 'a'
  answer(Char.is_eq(c, 'a'))

def main() -> Answer:
  bound()
