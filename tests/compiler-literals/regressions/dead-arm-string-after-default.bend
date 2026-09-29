import Base

# A String arm after a catch-all is unreachable, so its ill-typed body is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(s: String) -> U32:
  match s:
    case _: 0
    case "a": 'c'

def main() -> Answer:
  answer(U32.is_eq(pick("a"), 0))
