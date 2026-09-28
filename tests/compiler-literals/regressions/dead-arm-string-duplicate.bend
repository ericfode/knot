import Base

# The second `case "a"` is unreachable, so its ill-typed body is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(s: String) -> U32:
  match s:
    case "a": 0
    case "a": 1n
    case _: 2

def main() -> Answer:
  answer(U32.is_eq(pick("a"), 0))
